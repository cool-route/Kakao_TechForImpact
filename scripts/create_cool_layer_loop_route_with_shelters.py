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

nodes_path = (
    BASE_DIR
    / "data"
    / "nodes_with_score.geojson"
)

edges_path = (
    BASE_DIR
    / "data"
    / "sujiku_edges_5186.geojson"
)

shelters_path = (
    BASE_DIR
    / "data"
    / "shelters.json"
)

output_dir = (
    BASE_DIR
    / "outputs"
)

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
    score = np.nanmean([score_u, score_v])
    edge_scores.append(score)

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

    # fallback 그래프: q4 이하
    if edge_heat <= q4:
        if edge_heat <= q1:
            multiplier_fb = 0.2
        elif edge_heat <= q2:
            multiplier_fb = 0.8
        elif edge_heat <= q3:
            multiplier_fb = 3.0
        else:
            multiplier_fb = 10.0

        G_fallback.add_edge(
            u, v,
            weight=row["length"] * multiplier_fb,
            length=row["length"],
            heat_score=edge_heat,
            geometry=row.geometry
        )

    # 메인 그래프: q3 이하
    if edge_heat > q3:
        continue

    if edge_heat <= q1:
        multiplier = 0.2
    elif edge_heat <= q2:
        multiplier = 0.8
    else:
        multiplier = 3.0

    weight = row["length"] * multiplier

    G.add_edge(
        u, v,
        weight=weight,
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
    idx   = int(np.argmin(dists))
    return node_osmids[idx]

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
# 7-T. 쉼터 주변 시원한 출발점 후보 생성
# =========================================

node_heat_map  = dict(zip(nodes["osmid"].values, nodes["heat_score"].values))
cool_threshold = nodes["heat_score"].quantile(0.6)

def get_cool_nodes_near_shelter(shelter_node, graph, top_k=8):
    visited = set()
    queue   = [shelter_node]
    visited.add(shelter_node)
    candidates = []
    max_bfs = 300

    while queue and len(visited) < max_bfs:
        cur = queue.pop(0)
        heat = node_heat_map.get(cur, 999)

        if heat <= cool_threshold and graph.degree(cur) > 0:
            candidates.append((cur, heat))

        for nxt in graph.neighbors(cur):
            if nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)

    candidates.sort(key=lambda x: x[1])
    return [c[0] for c in candidates[:top_k]]

# =========================================
# 8. 쉼터를 공간 그리드로 분할해 지역별 후보 구성
# ★ 변경: n_regions 30 → 40 (더 세밀한 분산)
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
# 9. 쉼터 N개 경유 사이클 탐색
# ★ 변경: max_length 파라미터 추가 → 10km 상한 적용
# =========================================

MAX_ROUTE_LENGTH = 10000  # ★ 요구2: 최대 경로 길이 10km

def find_cycle_with_shelters(
    G,
    start_node,
    required_shelters,
    shelter_node_set,
    max_steps=10000,
    min_edges=5,
    max_length=MAX_ROUTE_LENGTH   # ★ 추가: 거리 상한
):
    COOL_NEIGHBOR_TOPK = 6

    init_shelters = frozenset([start_node]) if start_node in shelter_node_set else frozenset()

    stack = [(
        start_node,
        [start_node],
        set(),
        0.0,
        init_shelters
    )]

    best_result = None
    steps = 0

    while stack and steps < max_steps:
        steps += 1
        current, path, visited_edges, total_length, visited_shelters = stack.pop()

        # 사이클 완성 체크
        if (
            len(path) > min_edges
            and current == start_node
            and len(visited_shelters) >= required_shelters
        ):
            best_result = (path, total_length, visited_shelters)
            break

        # ★ 거리 상한 초과 시 가지치기
        if total_length > max_length:
            continue

        neighbors = list(G.neighbors(current))
        neighbors.sort(key=lambda n: G[current][n]["heat_score"])
        neighbors = neighbors[:COOL_NEIGHBOR_TOPK]

        if (
            start_node in G.neighbors(current)
            and start_node not in neighbors
        ):
            neighbors.append(start_node)

        for nxt in neighbors:
            edge_key = tuple(sorted((current, nxt)))

            if edge_key in visited_edges:
                continue

            edge_data  = G[current][nxt]
            new_length = total_length + edge_data["length"]

            # ★ 다음 이동 후에도 상한 초과하면 스킵
            if new_length > max_length and nxt != start_node:
                continue

            if nxt == start_node:
                new_shelters_check = (
                    visited_shelters | {nxt}
                    if nxt in shelter_node_set
                    else visited_shelters
                )
                if len(new_shelters_check) < required_shelters:
                    continue

            new_visited  = visited_edges | {edge_key}
            new_path     = path + [nxt]
            new_shelters = (
                visited_shelters | {nxt}
                if nxt in shelter_node_set
                else visited_shelters
            )

            stack.append((nxt, new_path, new_visited, new_length, new_shelters))

    return best_result if best_result else (None, 0, frozenset())


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
        route_nodes_gdf = gpd.GeoDataFrame(route_node_rows, crs="EPSG:4326")
        route_nodes_gdf.to_file(
            str(output_path_prefix) + "_nodes.geojson",
            driver="GeoJSON"
        )

    edge_records = []
    for i in range(len(path_nodes) - 1):
        u = path_nodes[i]
        v = path_nodes[i + 1]
        if G.has_edge(u, v):
            ed = G[u][v]
            edge_records.append({
                "u": u,
                "v": v,
                "length": ed["length"],
                "heat_score": ed["heat_score"],
                "geometry": ed["geometry"]
            })

    if edge_records:
        route_edges_gdf = gpd.GeoDataFrame(edge_records, crs="EPSG:4326")
        route_edges_gdf.to_file(
            str(output_path_prefix) + "_edges.geojson",
            driver="GeoJSON"
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
# ★ 변경1: global_used_regions 대신
#           global_used_shelter_nodes 로 쉼터 단위 블랙리스트
#           → 특정 쉼터(풍덕천 등) 반복 선택 원천 차단
# ★ 변경2: 각 n_shelters 루프마다 지역 순서를 새로 섞되
#           전체 사용 쉼터 노드만 공유
# =========================================

# ★ 전체 실행에서 사용된 앵커 쉼터 노드 블랙리스트
global_used_shelter_nodes = set()
# ★ 전체 실행에서 사용된 출발 노드
global_used_starts = set()

for (n_shelters, _) in shelter_targets:

    print(f"\n{'='*40}")
    print(f"쉼터 {n_shelters}개 경유 경로 {ROUTES_PER_GROUP}개 생성")
    print(f"{'='*40}")

    found_count = 0

    rng = random.Random()
    region_order = list(range(len(shelter_region_groups)))
    rng.shuffle(region_order)

    for region_idx in region_order:

        if found_count >= ROUTES_PER_GROUP:
            break

        region_shelters = shelter_region_groups[region_idx]

        region_shelters_shuffled = list(region_shelters)
        rng.shuffle(region_shelters_shuffled)

        succeeded = False

        for anchor_shelter in region_shelters_shuffled:

            anchor_node = anchor_shelter["node"]

            # ★ 이미 사용된 쉼터 노드 스킵 (풍덕천 반복 방지)
            if anchor_node in global_used_shelter_nodes:
                continue

            start_candidates = get_cool_nodes_near_shelter(
                anchor_node, G, top_k=8
            )
            if not start_candidates:
                start_candidates = get_cool_nodes_near_shelter(
                    anchor_node, G_fallback, top_k=8
                )

            if not start_candidates:
                continue

            rng.shuffle(start_candidates)

            for start_node in start_candidates:

                # ★ 전체 실행에서 사용된 출발점 스킵
                if start_node in global_used_starts:
                    continue

                print(f"  출발점 시도: {start_node} "
                      f"(지역 {region_idx}, 쉼터: {anchor_shelter['name']})")

                # 1차: 메인 그래프(파·초·노)
                result_path, result_length, result_shelters = (None, 0, frozenset())
                used_graph = G

                if start_node in G.nodes and G.degree(start_node) > 0:
                    result_path, result_length, result_shelters = find_cycle_with_shelters(
                        G,
                        start_node,
                        n_shelters,
                        shelter_node_set,
                        max_steps=10000,
                        min_edges=5,
                        max_length=MAX_ROUTE_LENGTH
                    )

                # 2차: fallback(파·초·노·주황)
                if result_path is None:
                    print(f"  → 메인 실패, fallback 재시도...")
                    used_graph = G_fallback
                    result_path, result_length, result_shelters = find_cycle_with_shelters(
                        G_fallback,
                        start_node,
                        n_shelters,
                        shelter_node_set,
                        max_steps=10000,
                        min_edges=5,
                        max_length=MAX_ROUTE_LENGTH
                    )

                if result_path is None:
                    print(f"  → 실패")
                    continue

                graph_label = "파·초·노" if used_graph is G else "파·초·노·주황"
                print(f"  → 성공! [{graph_label}] 거리: {result_length:.1f}m "
                      f"| 경유 쉼터: {len(result_shelters)}개 "
                      f"| 노드 수: {len(result_path)}")

                # ★ 전역 블랙리스트 등록
                global_used_shelter_nodes.add(anchor_node)
                global_used_starts.add(start_node)

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
                    mid_idx = len(all_coords) // 2
                    mid_lat, mid_lng = all_coords[mid_idx]

                km_label = f"{result_length / 1000:.2f} km"

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
                            ">{km_label}</div>
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
                succeeded = True
                break  # 출발점 루프 탈출

            if succeeded:
                break  # 쉼터 루프 탈출 → 다음 지역으로

    print(f"\n쉼터 {n_shelters}개 경유: {found_count}/{ROUTES_PER_GROUP}개 생성 완료")

print("\n\n✅ 전체 완료")