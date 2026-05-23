from pathlib import Path
import json

import geopandas as gpd
import networkx as nx
import numpy as np
import folium
import random
from shapely.geometry import mapping, LineString, Point

# =========================================
# 0. 프로젝트 경로
# =========================================

BASE_DIR = Path(__file__).resolve().parent.parent

nodes_path   = BASE_DIR / "data" / "nodes_with_score.geojson"
edges_path   = BASE_DIR / "data" / "sujiku_edges_5186.geojson"
shelters_path = BASE_DIR / "data" / "shelters.json"
output_dir   = BASE_DIR / "outputs"
output_dir.mkdir(exist_ok=True)

# =========================================
# 1. 데이터 읽기
# =========================================

nodes = gpd.read_file(nodes_path)
edges = gpd.read_file(edges_path)

nodes = nodes.to_crs(epsg=4326)
edges = edges.to_crs(epsg=4326)

print("노드 개수:", len(nodes))
print("엣지 개수:", len(edges))

with open(shelters_path, encoding="utf-8") as f:
    shelters_raw = json.load(f)

if isinstance(shelters_raw, list):
    shelters_list = shelters_raw
else:
    shelters_list = next(iter(shelters_raw.values()))

print(f"쉼터 개수: {len(shelters_list)}")

# =========================================
# 2. heat score dict
# =========================================

score_map = dict(zip(nodes["osmid"], nodes["heat_score"]))

# =========================================
# 3. 엣지 heat score 계산
# =========================================

edge_scores = []
for idx, edge in edges.iterrows():
    u = edge["u"]
    v = edge["v"]
    score_u = score_map.get(u, np.nan)
    score_v = score_map.get(v, np.nan)
    edge_scores.append(np.nanmean([score_u, score_v]))
edges["heat_score"] = edge_scores

# =========================================
# 4. 분위수 계산
# =========================================

q1 = edges["heat_score"].quantile(0.2)
q2 = edges["heat_score"].quantile(0.4)
q3 = edges["heat_score"].quantile(0.6)
q4 = edges["heat_score"].quantile(0.8)

print("\n===== 분위수 =====")
print(q1, q2, q3, q4)

# =========================================
# 5. 그래프 생성
# =========================================

G = nx.Graph()
for idx, row in nodes.iterrows():
    G.add_node(
        row["osmid"],
        x=row.geometry.x,
        y=row.geometry.y,
        heat_score=row["heat_score"]
    )

# =========================================
# 6. 엣지 추가 (메인 + fallback)
# ★ 변경: 메인을 q4 이하까지 확대 → 성공률 향상
#          fallback은 전체 엣지 허용 (빨간 길 포함, 초고 페널티)
# =========================================

G_fallback = nx.Graph()

for idx, row in edges.iterrows():

    u = row["u"]
    v = row["v"]

    if u not in G.nodes or v not in G.nodes:
        continue
    if row.geometry is None:
        continue

    edge_heat = row["heat_score"]
    if np.isnan(edge_heat):
        edge_heat = 999

    # ★ fallback: 전체 엣지 (빨간 길도 포함, 초고 페널티)
    if edge_heat <= q1:
        mult_fb = 0.2
    elif edge_heat <= q2:
        mult_fb = 0.8
    elif edge_heat <= q3:
        mult_fb = 3.0
    elif edge_heat <= q4:
        mult_fb = 10.0
    else:
        mult_fb = 50.0  # 빨간 길: 탐색은 허용하되 매우 높은 페널티

    G_fallback.add_edge(
        u, v,
        weight=row["length"] * mult_fb,
        length=row["length"],
        heat_score=edge_heat,
        geometry=row.geometry
    )

    # ★ 메인: q4 이하 (기존 q3→q4로 확대)
    if edge_heat > q4:
        continue

    if edge_heat <= q1:
        multiplier = 0.2
    elif edge_heat <= q2:
        multiplier = 0.8
    elif edge_heat <= q3:
        multiplier = 3.0
    else:                  # q3 < score <= q4 (주황)
        multiplier = 10.0

    G.add_edge(
        u, v,
        weight=row["length"] * multiplier,
        length=row["length"],
        heat_score=edge_heat,
        geometry=row.geometry
    )

for idx, row in nodes.iterrows():
    if row["osmid"] not in G_fallback.nodes:
        G_fallback.add_node(
            row["osmid"],
            x=row.geometry.x,
            y=row.geometry.y,
            heat_score=row["heat_score"]
        )

print("\n그래프 생성 완료")
print("메인 그래프  - 노드:", G.number_of_nodes(), "/ 엣지:", G.number_of_edges())
print("Fallback 그래프 - 노드:", G_fallback.number_of_nodes(), "/ 엣지:", G_fallback.number_of_edges())

# =========================================
# 7. 색상 함수
# =========================================

def get_color(score):
    if score <= q1:
        return "blue"
    elif score <= q2:
        return "green"
    elif score <= q3:
        return "yellow"
    elif score <= q4:
        return "orange"
    else:
        return "red"

# =========================================
# 7-S. 쉼터 → 가장 가까운 노드 스냅
# =========================================

node_osmids = nodes["osmid"].values
node_lons   = nodes.geometry.x.values
node_lats   = nodes.geometry.y.values

def snap_to_node(lat, lon):
    dists = (node_lats - lat) ** 2 + (node_lons - lon) ** 2
    return node_osmids[int(np.argmin(dists))]

shelters = []
for s in shelters_list:
    snapped = snap_to_node(s["lat"], s["lon"])
    shelters.append({
        "name":    s.get("name", "쉼터"),
        "type":    s.get("type", ""),
        "address": s.get("address", ""),
        "lat":     s["lat"],
        "lon":     s["lon"],
        "node":    snapped,
    })

shelter_node_set = set(s["node"] for s in shelters)
shelter_node_map = {}
for s in shelters:
    if s["node"] not in shelter_node_map:
        shelter_node_map[s["node"]] = s

print(f"스냅 완료: 쉼터 {len(shelters)}개 → 유니크 노드 {len(shelter_node_map)}개")

# =========================================
# 7-T. 노드 heat 맵
# =========================================

node_heat_map = dict(zip(nodes["osmid"].values, nodes["heat_score"].values))

# =========================================
# 8. ★ 출발점 후보: 쉼터 기준 BFS 대신
#       전체 노드를 공간 그리드로 나눠 지역별 시원한 노드 풀 생성
#       → 특정 쉼터 주변에만 출발점이 몰리는 문제 해결
# =========================================

def get_start_candidate_pool(nodes_gdf, G_ref, n_regions=40, top_k_per_region=6):
    """
    전체 노드를 공간 그리드로 나눠 각 셀에서
    heat_score 낮고 graph degree > 0 인 노드 top_k개씩 수집.
    반환: { region_idx: [osmid, ...] }
    """
    cool_q = nodes_gdf["heat_score"].quantile(0.5)   # 하위 50% 이내
    cool_nodes = nodes_gdf[
        (nodes_gdf["heat_score"] <= cool_q)
    ].copy()

    minx = cool_nodes.geometry.x.min()
    maxx = cool_nodes.geometry.x.max()
    miny = cool_nodes.geometry.y.min()
    maxy = cool_nodes.geometry.y.max()

    grid_cols = int(np.ceil(np.sqrt(n_regions)))
    grid_rows = int(np.ceil(n_regions / grid_cols))

    x_bins = np.linspace(minx, maxx, grid_cols + 1)
    y_bins = np.linspace(miny, maxy, grid_rows + 1)

    pool = {}   # region_idx → list of osmid
    idx  = 0

    for r in range(grid_rows):
        for c in range(grid_cols):
            mask = (
                (cool_nodes.geometry.x >= x_bins[c]) &
                (cool_nodes.geometry.x <  x_bins[c + 1]) &
                (cool_nodes.geometry.y >= y_bins[r]) &
                (cool_nodes.geometry.y <  y_bins[r + 1])
            )
            cell = cool_nodes[mask]
            if cell.empty:
                idx += 1
                continue

            # degree > 0 필터
            valid = [
                row["osmid"] for _, row in cell.iterrows()
                if G_ref.degree(row["osmid"]) > 0
            ]
            if not valid:
                idx += 1
                continue

            # heat 낮은 순 정렬
            valid_sorted = sorted(valid, key=lambda n: node_heat_map.get(n, 999))
            pool[idx] = valid_sorted[:top_k_per_region]
            idx += 1

    return pool


start_pool = get_start_candidate_pool(nodes, G, n_regions=40, top_k_per_region=6)
print(f"출발점 후보 지역 수: {len(start_pool)}")

# =========================================
# 8-S. 쉼터 공간 그리드 (쉼터 근접성 확인용)
# =========================================

def get_shelter_region_groups(shelters, n_regions=40):
    lons = np.array([s["lon"] for s in shelters])
    lats = np.array([s["lat"] for s in shelters])

    minx, maxx = lons.min(), lons.max()
    miny, maxy = lats.min(), lats.max()

    grid_cols = int(np.ceil(np.sqrt(n_regions)))
    grid_rows = int(np.ceil(n_regions / grid_cols))

    x_bins = np.linspace(minx, maxx, grid_cols + 1)
    y_bins = np.linspace(miny, maxy, grid_rows + 1)

    groups = []
    for r in range(grid_rows):
        for c in range(grid_cols):
            cell = [
                s for s in shelters
                if x_bins[c] <= s["lon"] < x_bins[c + 1]
                and y_bins[r] <= s["lat"] < y_bins[r + 1]
            ]
            if cell:
                groups.append(cell)

    return groups

shelter_region_groups = get_shelter_region_groups(shelters, n_regions=40)
print(f"쉼터 지역 그룹 수: {len(shelter_region_groups)}")

# =========================================
# 9. ★ 쉼터 N개 경유 사이클 탐색
#    문제1 해결: max_steps 대폭 증가 + 탐색 효율화
#    문제2 해결: max_length 제거, max_edges로 대체
#               (엣지 수 제한 → 자연스러운 길이 분포)
# =========================================

def find_cycle_with_shelters(
    G,
    start_node,
    required_shelters,
    shelter_node_set,
    max_steps=30000,     # ★ 10000 → 30000
    min_edges=4,
    max_edges=80,        # ★ max_length 대신 max_edges로 경로 길이 간접 제어
):
    COOL_NEIGHBOR_TOPK = 6

    init_shelters = frozenset([start_node]) if start_node in shelter_node_set else frozenset()

    # 스택: (current, path_tuple, visited_edges_frozenset, total_length, visited_shelters)
    stack = [(
        start_node,
        (start_node,),
        frozenset(),
        0.0,
        init_shelters
    )]

    steps = 0

    while stack and steps < max_steps:
        steps += 1
        current, path, visited_edges, total_length, visited_shelters = stack.pop()

        # 사이클 완성 체크
        if (
            len(path) > min_edges + 1
            and current == start_node
            and len(visited_shelters) >= required_shelters
        ):
            return (list(path), total_length, visited_shelters)

        # ★ 엣지 수 상한 초과 가지치기
        if len(path) > max_edges:
            continue

        neighbors = list(G.neighbors(current))
        neighbors.sort(key=lambda n: G[current][n]["heat_score"])
        neighbors = neighbors[:COOL_NEIGHBOR_TOPK]

        # 출발점 복귀 기회 보장
        if (
            start_node in G.neighbors(current)
            and start_node not in neighbors
        ):
            neighbors.append(start_node)

        for nxt in neighbors:
            edge_key = (min(current, nxt), max(current, nxt))

            if edge_key in visited_edges:
                continue

            edge_data  = G[current][nxt]
            new_length = total_length + edge_data["length"]

            # 출발점 복귀 조건
            if nxt == start_node:
                new_shelters_check = (
                    visited_shelters | frozenset([nxt])
                    if nxt in shelter_node_set
                    else visited_shelters
                )
                if len(new_shelters_check) < required_shelters:
                    continue

            new_shelters = (
                visited_shelters | frozenset([nxt])
                if nxt in shelter_node_set
                else visited_shelters
            )

            stack.append((
                nxt,
                path + (nxt,),
                visited_edges | frozenset([edge_key]),
                new_length,
                new_shelters
            ))

    return (None, 0, frozenset())

# =========================================
# 10. GeoJSON 저장 함수
# =========================================

def save_route_geojson(path_nodes, G, nodes_gdf, output_path_prefix):
    route_node_rows = []
    for osmid in path_nodes:
        row = nodes_gdf[nodes_gdf["osmid"] == osmid]
        if not row.empty:
            route_node_rows.append(row.iloc[0])

    if route_node_rows:
        gpd.GeoDataFrame(route_node_rows, crs="EPSG:4326").to_file(
            str(output_path_prefix) + "_nodes.geojson", driver="GeoJSON"
        )

    edge_records = []
    for i in range(len(path_nodes) - 1):
        u = path_nodes[i]
        v = path_nodes[i + 1]
        if G.has_edge(u, v):
            ed = G[u][v]
            edge_records.append({
                "u": u, "v": v,
                "length": ed["length"],
                "heat_score": ed["heat_score"],
                "geometry": ed["geometry"]
            })

    if edge_records:
        gpd.GeoDataFrame(edge_records, crs="EPSG:4326").to_file(
            str(output_path_prefix) + "_edges.geojson", driver="GeoJSON"
        )

# =========================================
# 11. 목표 정의: 쉼터 수별 2개씩, 총 10개
# =========================================

shelter_targets = [
    (1, 2),
    (2, 2),
    (3, 2),
    (4, 2),
    (5, 2),
]

ROUTES_PER_GROUP = 2

# =========================================
# 13. 경로 생성 메인 루프
# ★ 문제3 해결:
#   - 출발점을 전체 그리드 풀(start_pool)에서 선택
#   - 블랙리스트를 앵커 쉼터 단위가 아닌 start_node 단위로만 관리
#   - n_shelters 루프마다 지역 순서 새로 섞기
#   - 두 번째 경로는 첫 번째와 다른 지역 그룹 강제
# =========================================

global_used_starts   = set()   # 전체 실행에서 사용된 출발 노드

for (n_shelters, _) in shelter_targets:

    print(f"\n{'='*40}")
    print(f"쉼터 {n_shelters}개 경유 경로 {ROUTES_PER_GROUP}개 생성")
    print(f"{'='*40}")

    found_count = 0
    local_used_regions = set()   # ★ 이 n_shelters 내에서 사용된 지역

    rng = random.Random()

    # 지역 순서 섞기 (실행마다 다양한 위치)
    region_order = list(start_pool.keys())
    rng.shuffle(region_order)

    for region_idx in region_order:

        if found_count >= ROUTES_PER_GROUP:
            break

        # ★ 같은 n_shelters 루프 내 지역 재사용 금지
        if region_idx in local_used_regions:
            continue

        candidates = list(start_pool[region_idx])
        rng.shuffle(candidates)

        for start_node in candidates:

            if start_node in global_used_starts:
                continue

            if G.degree(start_node) == 0:
                continue

            print(f"  출발점 시도: {start_node} (지역 {region_idx})")

            # 1차: 메인 그래프(q4 이하)
            result_path, result_length, result_shelters = find_cycle_with_shelters(
                G,
                start_node,
                n_shelters,
                shelter_node_set,
                max_steps=30000,
                min_edges=4,
                max_edges=80
            )

            # 2차: fallback(전체 엣지)
            if result_path is None:
                print(f"  → 메인 실패, fallback 재시도...")
                result_path, result_length, result_shelters = find_cycle_with_shelters(
                    G_fallback,
                    start_node,
                    n_shelters,
                    shelter_node_set,
                    max_steps=30000,
                    min_edges=4,
                    max_edges=80
                )
                used_graph = G_fallback
            else:
                used_graph = G

            if result_path is None:
                print(f"  → 실패")
                continue

            graph_label = "메인(q4↓)" if used_graph is G else "fallback(전체)"
            print(f"  → 성공! [{graph_label}] 거리: {result_length:.1f}m "
                  f"| 경유 쉼터: {len(result_shelters)}개 "
                  f"| 노드 수: {len(result_path)}")

            global_used_starts.add(start_node)
            local_used_regions.add(region_idx)

            route_id = f"shelter{n_shelters}_route{found_count + 1}"

            # ---------------------------
            # 지도 생성 (HTML)
            # ---------------------------

            start_geom = nodes[nodes["osmid"] == start_node].geometry.iloc[0]

            m = folium.Map(
                location=[start_geom.y, start_geom.x],
                zoom_start=15,
                tiles=None
            )
            folium.TileLayer(
                tiles="OpenStreetMap",
                opacity=0.5,
                name="background"
            ).add_to(m)

            mid_lat, mid_lng = start_geom.y, start_geom.x
            all_coords = []

            for i in range(len(result_path) - 1):
                u = result_path[i]
                v = result_path[i + 1]
                if not used_graph.has_edge(u, v):
                    continue

                edge_data = used_graph[u][v]
                geom      = edge_data["geometry"]
                score     = edge_data["heat_score"]
                color     = get_color(score)

                if geom.geom_type == "LineString":
                    coords = [[y, x] for x, y in geom.coords]
                    all_coords.extend(coords)
                    folium.PolyLine(
                        locations=coords,
                        color=color,
                        weight=6,
                        opacity=0.95,
                        tooltip=f"Heat Score: {score:.2f}"
                    ).add_to(m)

            if all_coords:
                mid_lat, mid_lng = all_coords[len(all_coords) // 2]

            folium.Marker(
                location=[mid_lat, mid_lng],
                icon=folium.DivIcon(
                    html=f"""
                        <div style="
                            background-color: white;
                            border: 1.5px solid #333;
                            border-radius: 3px;
                            padding: 2px 5px;
                            font-size: 11px;
                            font-weight: bold;
                            color: #222;
                            white-space: nowrap;
                            box-shadow: 1px 1px 3px rgba(0,0,0,0.3);
                        ">{result_length / 1000:.2f} km</div>
                    """,
                    icon_size=(60, 22),
                    icon_anchor=(30, 11),
                )
            ).add_to(m)

            folium.Marker(
                location=[start_geom.y, start_geom.x],
                tooltip=f"출발/도착 | 쉼터{n_shelters}개 | {result_length:.0f}m",
                icon=folium.Icon(color="green")
            ).add_to(m)

            for node_osmid in result_shelters:
                if node_osmid not in shelter_node_map:
                    continue
                s = shelter_node_map[node_osmid]
                popup_html = f"""
                    <div style="font-size:13px; min-width:180px;">
                        <b>{s['name']}</b><br>
                        <span style="color:#555;">종류: {s['type']}</span><br>
                        <span style="color:#555;">주소: {s['address']}</span>
                    </div>
                """
                folium.Marker(
                    location=[s["lat"], s["lon"]],
                    tooltip=s["name"],
                    popup=folium.Popup(popup_html, max_width=260),
                    icon=folium.Icon(color="blue", icon="home", prefix="fa")
                ).add_to(m)

            html_path = output_dir / f"cool_cycle_{route_id}.html"
            m.save(str(html_path))
            print(f"  → HTML 저장: {html_path.name}")

            geojson_prefix = output_dir / f"cool_cycle_{route_id}"
            save_route_geojson(result_path, used_graph, nodes, geojson_prefix)
            print(f"  → GeoJSON 저장: cool_cycle_{route_id}_nodes/edges.geojson")

            found_count += 1
            break  # 다음 지역으로

    print(f"\n쉼터 {n_shelters}개 경유: {found_count}/{ROUTES_PER_GROUP}개 생성 완료")

print("\n\n✅ 전체 완료")