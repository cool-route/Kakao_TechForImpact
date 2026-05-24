from pathlib import Path

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
# 6. 엣지 추가
# ★ 변경: heat_score > q2 인 엣지(노란색·주황색·빨간색)
#         그래프에 아예 추가하지 않음 → 파란/초록 길만 사용
#         단, q2 초과 엣지가 너무 많아 경로 생성 실패 시
#         fallback으로 q3 이하까지 허용하는 G_fallback도 생성
# =========================================

G_fallback = nx.Graph()  # ★ fallback: q3 이하까지 허용

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

    # ★ fallback 그래프: q3 이하(파랑·초록·노랑)까지
    if edge_heat <= q3:
        if edge_heat <= q1:
            multiplier_fb = 0.3
        elif edge_heat <= q2:
            multiplier_fb = 0.8
        else:
            multiplier_fb = 5.0

        G_fallback.add_edge(
            u, v,
            weight=row["length"] * multiplier_fb,
            length=row["length"],
            heat_score=edge_heat,
            geometry=row.geometry
        )

    # ★ 메인 그래프: q2 이하(파랑·초록)만
    if edge_heat > q2:
        continue

    if edge_heat <= q1:
        multiplier = 0.2   # ★ 파란 길 더 강하게 우선 (0.3 → 0.2)
    elif edge_heat <= q2:
        multiplier = 1.0   # ★ 초록 길 (0.8 → 1.0으로 소폭 조정)

    weight = row["length"] * multiplier

    G.add_edge(
        u,
        v,
        weight=weight,
        length=row["length"],
        heat_score=edge_heat,
        geometry=row.geometry
    )

# fallback 그래프에도 노드 추가
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
# 8. 지역 분산을 위한 공간 그리드 분할
# =========================================

def get_region_candidates(nodes_gdf, n_regions=12, candidates_per_region=5, heat_threshold=None):
    if heat_threshold is None:
        heat_threshold = nodes_gdf["heat_score"].quantile(0.4)

    cool = nodes_gdf[nodes_gdf["heat_score"] <= heat_threshold].copy()

    minx = cool.geometry.x.min()
    maxx = cool.geometry.x.max()
    miny = cool.geometry.y.min()
    maxy = cool.geometry.y.max()

    grid_cols = int(np.ceil(np.sqrt(n_regions)))
    grid_rows = int(np.ceil(n_regions / grid_cols))

    x_bins = np.linspace(minx, maxx, grid_cols + 1)
    y_bins = np.linspace(miny, maxy, grid_rows + 1)

    region_candidates = []

    for r in range(grid_rows):
        for c in range(grid_cols):
            mask = (
                (cool.geometry.x >= x_bins[c]) &
                (cool.geometry.x < x_bins[c + 1]) &
                (cool.geometry.y >= y_bins[r]) &
                (cool.geometry.y < y_bins[r + 1])
            )
            cell = cool[mask]
            if len(cell) == 0:
                continue

            top = cell.nsmallest(candidates_per_region, "heat_score")
            region_candidates.append(top["osmid"].tolist())

    return region_candidates

# =========================================
# 9. 핵심: 단방향 사이클 경로 탐색
# ★ 변경: COOL_NEIGHBOR_TOPK를 4로 줄여
#         더 시원한 이웃에만 더욱 집중
# =========================================

def find_cycle_path(G, start_node, target_distance, tolerance=0.25, max_steps=5000):
    lower = target_distance * (1 - tolerance)
    upper = target_distance * (1 + tolerance)

    COOL_NEIGHBOR_TOPK = 4  # ★ 5 → 4 (더 시원한 쪽으로 집중)

    stack = [(start_node, [start_node], set(), 0.0)]

    best_result = None
    steps = 0

    while stack and steps < max_steps:
        steps += 1
        current, path, visited_edges, total_length = stack.pop()

        if (
            len(path) > 2
            and current == start_node
            and lower <= total_length <= upper
        ):
            best_result = (path, total_length)
            break

        if total_length > upper:
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

            edge_data = G[current][nxt]
            new_length = total_length + edge_data["length"]

            if new_length > upper and nxt != start_node:
                continue

            if nxt == start_node:
                if new_length < lower:
                    continue

            new_visited = visited_edges | {edge_key}
            new_path = path + [nxt]

            stack.append((nxt, new_path, new_visited, new_length))

    return best_result if best_result else (None, 0)


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
# 11. 목표 거리 & 경로 수
# =========================================

targets = {
    "1km": 1000,
    "3km": 3000,
    "5km": 5000,
    "7km": 7000,
}

ROUTES_PER_TARGET = 3

# =========================================
# 12. 지역별 출발점 후보 준비
# =========================================

region_candidates_list = get_region_candidates(
    nodes,
    n_regions=24,
    candidates_per_region=10,
    heat_threshold=nodes["heat_score"].quantile(0.2)
)

print(f"\n지역 그룹 수: {len(region_candidates_list)}")

# =========================================
# 13. 경로 생성 메인 루프
# ★ 변경: 메인 그래프(파랑·초록)로 먼저 시도,
#         실패 시 fallback 그래프(+노랑)로 재시도
# =========================================

for route_name, target_distance in targets.items():

    print(f"\n{'='*40}")
    print(f"거리 목표: {route_name} ({target_distance}m)")
    print(f"{'='*40}")

    found_count = 0
    used_regions = set()
    used_starts = set()

    region_order = list(range(len(region_candidates_list)))
    rng = random.Random()
    rng.shuffle(region_order)

    for region_idx in region_order:

        if found_count >= ROUTES_PER_TARGET:
            break

        if region_idx in used_regions:
            continue

        candidates = region_candidates_list[region_idx]
        candidates = list(candidates)
        rng.shuffle(candidates)

        for start_node in candidates:

            if start_node not in G.nodes and start_node not in G_fallback.nodes:
                continue

            if start_node in used_starts:
                continue

            if G.degree(start_node) == 0 and G_fallback.degree(start_node) == 0:
                continue

            print(f"  출발점 시도: {start_node} (지역 {region_idx})")

            # ★ 1차: 메인 그래프(파랑·초록)로 시도
            result_path, result_length = (None, 0)
            used_graph = G

            if start_node in G.nodes and G.degree(start_node) > 0:
                result_path, result_length = find_cycle_path(
                    G,
                    start_node,
                    target_distance,
                    tolerance=0.25,
                    max_steps=5000
                )

            # ★ 2차: 실패 시 fallback 그래프(+노랑)로 재시도
            if result_path is None:
                print(f"  → 메인 실패, fallback(+노랑) 재시도...")
                used_graph = G_fallback
                result_path, result_length = find_cycle_path(
                    G_fallback,
                    start_node,
                    target_distance,
                    tolerance=0.25,
                    max_steps=5000
                )

            if result_path is None:
                print(f"  → 실패")
                continue

            graph_label = "파랑·초록" if used_graph is G else "파랑·초록·노랑"
            print(f"  → 성공! [{graph_label}] 실제 거리: {result_length:.1f}m, 노드 수: {len(result_path)}")

            used_regions.add(region_idx)
            used_starts.add(start_node)

            route_id = f"{route_name}_route{found_count + 1}"

            # ---------------------------
            # 지도 생성 (HTML)
            # ★ 변경: 배경 지도 opacity 낮춤 (0.5)
            # ---------------------------

            start_geom = nodes[nodes["osmid"] == start_node].geometry.iloc[0]

            m = folium.Map(
                location=[start_geom.y, start_geom.x],
                zoom_start=15,
                tiles=None   # ★ 기본 타일 비활성화 후 opacity 지정 타일로 교체
            )

            # ★ 배경 지도 투명도 0.5 적용
            folium.TileLayer(
                tiles="OpenStreetMap",
                opacity=0.5,       # ★ 배경 흐리게 (1.0이 기본)
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
                geom = edge_data["geometry"]
                score = edge_data["heat_score"]
                color = get_color(score)

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
                tooltip=f"출발/도착 | {route_name} | {result_length:.0f}m",
                icon=folium.Icon(color="green")
            ).add_to(m)

            html_path = output_dir / f"cool_cycle_{route_id}.html"
            m.save(str(html_path))
            print(f"  → HTML 저장: {html_path.name}")

            geojson_prefix = output_dir / f"cool_cycle_{route_id}"
            save_route_geojson(result_path, used_graph, nodes, geojson_prefix)
            print(f"  → GeoJSON 저장: cool_cycle_{route_id}_nodes/edges.geojson")

            found_count += 1
            break

    print(f"\n{route_name}: {found_count}/{ROUTES_PER_TARGET}개 생성 완료")

print("\n\n✅ 전체 완료")