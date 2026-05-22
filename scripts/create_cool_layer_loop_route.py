from pathlib import Path

import geopandas as gpd
import networkx as nx
import numpy as np
import folium
import random

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

output_dir.mkdir(
    exist_ok=True
)

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
# 6. 엣지 추가 (가중치 유지)
# =========================================

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

    # Heat penalty
    if edge_heat <= q1:
        multiplier = 0.3
    elif edge_heat <= q2:
        multiplier = 0.8
    elif edge_heat <= q3:
        multiplier = 2.5
    elif edge_heat <= q4:
        multiplier = 7
    else:
        multiplier = 20

    weight = row["length"] * multiplier

    G.add_edge(
        u,
        v,
        weight=weight,
        length=row["length"],
        heat_score=edge_heat,
        geometry=row.geometry
    )

print("\n그래프 생성 완료")
print("총 노드:", G.number_of_nodes())
print("총 엣지:", G.number_of_edges())

# =========================================
# 7. 시원한 출발점 후보 (공간적으로 분산)
# =========================================

cool_nodes = nodes[nodes["heat_score"] <= q2].copy()

# 전체 영역을 격자로 나눠 구역별로 후보 추출 → 다양성 확보
def get_spread_candidates(cool_nodes, n_zones=5, per_zone=6, seed=42):
    """
    노드 공간을 n_zones x n_zones 격자로 나눠
    각 구역에서 per_zone개씩 추출 → 전체적으로 분산된 후보 반환
    """
    rng = random.Random(seed)

    min_x = cool_nodes.geometry.x.min()
    max_x = cool_nodes.geometry.x.max()
    min_y = cool_nodes.geometry.y.min()
    max_y = cool_nodes.geometry.y.max()

    candidates = []

    for xi in range(n_zones):
        for yi in range(n_zones):

            x0 = min_x + (max_x - min_x) * xi / n_zones
            x1 = min_x + (max_x - min_x) * (xi + 1) / n_zones
            y0 = min_y + (max_y - min_y) * yi / n_zones
            y1 = min_y + (max_y - min_y) * (yi + 1) / n_zones

            zone_nodes = cool_nodes[
                (cool_nodes.geometry.x >= x0) &
                (cool_nodes.geometry.x < x1) &
                (cool_nodes.geometry.y >= y0) &
                (cool_nodes.geometry.y < y1)
            ]

            # 해당 구역에 그래프 연결된 노드만 필터
            zone_osmids = [
                n for n in zone_nodes["osmid"].tolist()
                if n in G.nodes and G.degree(n) >= 2
            ]

            if not zone_osmids:
                continue

            sampled = rng.sample(zone_osmids, min(per_zone, len(zone_osmids)))
            candidates.extend(sampled)

    rng.shuffle(candidates)
    return candidates


# =========================================
# 8. 목표 거리
# =========================================

targets = {
    "1km": 1000,
    "3km": 3000,
    "5km": 5000,
    "7km": 7000
}

# =========================================
# 9. 색상 함수
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
# 10. 핵심: 안정적인 단방향 사이클 생성
# =========================================

def build_cycle_path(G, start_node, target_distance, seed=0):
    """
    단방향 단일 사이클 경로를 생성한다.

    전략:
    1) 출발점에서 목표 거리의 ~75%까지 greedy DFS로 전진
       (U턴 방지 + 방문한 엣지 재사용 억제)
    2) 남은 거리를 Dijkstra 최단 경로로 start로 귀환
    3) 두 구간을 이어붙여 단일 원형 경로 완성

    반환: (path 노드 리스트, 실제 총 거리) 또는 (None, None)
    """

    rng = random.Random(seed)

    # --- Phase 1: greedy walk (목표의 75% 지점까지) ---

    path = [start_node]
    visited_edges = set()
    total_length = 0.0

    current = start_node
    prev = None  # U턴 방지용

    for _ in range(3000):

        # 목표 거리의 75% 이상 걸었으면 귀환 시작
        if total_length >= target_distance * 0.75:
            break

        neighbors = list(G.neighbors(current))
        rng.shuffle(neighbors)

        candidates = []

        for nxt in neighbors:

            # U턴 방지
            if nxt == prev:
                continue

            edge_key = tuple(sorted((current, nxt)))

            # 이미 사용한 엣지 제외
            if edge_key in visited_edges:
                continue

            if not G.has_edge(current, nxt):
                continue

            edge_data = G[current][nxt]
            candidates.append((edge_data["weight"], nxt, edge_data))

        if not candidates:
            # 막혔을 때: 방문 제한 완화 (U턴만 막고 재방문 허용)
            for nxt in neighbors:
                if nxt == prev:
                    continue
                if not G.has_edge(current, nxt):
                    continue
                edge_data = G[current][nxt]
                candidates.append((edge_data["weight"], nxt, edge_data))

        if not candidates:
            # 완전히 막힘 → 실패
            return None, None

        # 가장 시원한(weight 낮은) 엣지 선택
        candidates.sort(key=lambda x: x[0])

        # 상위 3개 중 랜덤 선택 (다양성)
        top_k = candidates[:3]
        _, best_next, best_data = rng.choice(top_k)

        visited_edges.add(tuple(sorted((current, best_next))))
        path.append(best_next)
        total_length += best_data["length"]

        prev = current
        current = best_next

    # --- Phase 2: Dijkstra로 start까지 귀환 ---

    if current == start_node:
        # 이미 돌아온 경우
        return path, total_length

    try:
        return_path = nx.shortest_path(
            G,
            source=current,
            target=start_node,
            weight="weight"
        )
    except nx.NetworkXNoPath:
        return None, None

    # 귀환 경로 이어붙이기 (current 중복 제거)
    for node in return_path[1:]:
        if not G.has_edge(current, node):
            return None, None
        edge_data = G[current][node]
        total_length += edge_data["length"]
        path.append(node)
        current = node

    # 최종 거리 범위 검증
    if not (target_distance * 0.7 <= total_length <= target_distance * 1.5):
        return None, None

    return path, total_length


# =========================================
# 11. 경로 3개 생성 (구역 분산 + 반복 시도)
# =========================================

NUM_ROUTES = 3          # 경로 몇 개 생성할지
MAX_ATTEMPTS = 80       # 출발점 후보 최대 시도 횟수

for route_name, target_distance in targets.items():

    print(f"\n{'='*40}")
    print(f"[{route_name}] 경로 {NUM_ROUTES}개 생성 시작")
    print(f"{'='*40}")

    # 매 거리마다 새 시드로 분산 후보 생성
    base_seed = hash(route_name) % 100000
    start_candidates = get_spread_candidates(
        cool_nodes,
        n_zones=5,
        per_zone=8,
        seed=base_seed
    )

    routes_found = []
    used_starts = set()

    attempt = 0
    cand_idx = 0

    while len(routes_found) < NUM_ROUTES and attempt < MAX_ATTEMPTS:

        if cand_idx >= len(start_candidates):
            # 후보 소진 시 재생성 (다른 시드)
            start_candidates = get_spread_candidates(
                cool_nodes,
                n_zones=5,
                per_zone=8,
                seed=base_seed + attempt
            )
            cand_idx = 0

        start_node = start_candidates[cand_idx]
        cand_idx += 1
        attempt += 1

        if start_node in used_starts:
            continue

        # 이미 찾은 경로의 출발점과 너무 가까우면 스킵 (다양성)
        if routes_found:
            sx = G.nodes[start_node].get("x", 0)
            sy = G.nodes[start_node].get("y", 0)
            too_close = False
            for prev_path, _ in routes_found:
                px = G.nodes[prev_path[0]].get("x", 0)
                py = G.nodes[prev_path[0]].get("y", 0)
                dist_deg = ((sx - px) ** 2 + (sy - py) ** 2) ** 0.5
                # 약 300m 이상 떨어져야 함 (1도 ≈ 111km → 0.003도 ≈ 330m)
                if dist_deg < 0.003:
                    too_close = True
                    break
            if too_close:
                continue

        path, actual_dist = build_cycle_path(
            G,
            start_node,
            target_distance,
            seed=base_seed + attempt
        )

        if path is None:
            continue

        used_starts.add(start_node)
        routes_found.append((path, actual_dist))

        print(f"  경로 {len(routes_found)} 발견 | 출발: {start_node} | 실제 거리: {actual_dist:.0f}m")

    # =========================================
    # 12. 지도 저장
    # =========================================

    if not routes_found:
        print(f"[{route_name}] 경로 생성 실패")
        continue

    # 경로별 색상
    route_colors = ["blue", "red", "purple"]
    route_labels = ["경로 A", "경로 B", "경로 C"]

    m = folium.Map(location=[37.32, 127.09], zoom_start=13)

    for r_idx, (path, actual_dist) in enumerate(routes_found):

        line_color = route_colors[r_idx % len(route_colors)]
        label = route_labels[r_idx % len(route_labels)]

        # 경로 폴리라인 그리기
        for i in range(len(path) - 1):

            u = path[i]
            v = path[i + 1]

            if not G.has_edge(u, v):
                continue

            edge_data = G[u][v]
            geom = edge_data["geometry"]
            score = edge_data["heat_score"]

            if geom.geom_type == "LineString":

                coords = [[y, x] for x, y in geom.coords]

                folium.PolyLine(
                    locations=coords,
                    color=line_color,
                    weight=5,
                    opacity=0.9,
                    tooltip=f"[{label}] Heat: {score:.2f} | 총 거리: {actual_dist:.0f}m"
                ).add_to(m)

        # 출발/도착 마커
        start_node = path[0]
        start_geom = nodes[nodes["osmid"] == start_node].geometry.iloc[0]

        marker_colors = ["green", "darkred", "darkpurple"]

        folium.Marker(
            location=[start_geom.y, start_geom.x],
            tooltip=f"{label} 출발/도착 | {actual_dist:.0f}m",
            icon=folium.Icon(color=marker_colors[r_idx % len(marker_colors)])
        ).add_to(m)

    output_path = output_dir / f"cool_cycle_{route_name}.html"
    m.save(output_path)

    print(f"[{route_name}] 지도 저장 완료 → {output_path}")
    print(f"  총 {len(routes_found)}개 경로 포함")