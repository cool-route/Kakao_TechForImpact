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

nodes = gpd.read_file(
    nodes_path
)

edges = gpd.read_file(
    edges_path
)

nodes = nodes.to_crs(epsg=4326)
edges = edges.to_crs(epsg=4326)

print("노드 개수:", len(nodes))
print("엣지 개수:", len(edges))

# =========================================
# 2. heat score dict
# =========================================

score_map = dict(
    zip(
        nodes["osmid"],
        nodes["heat_score"]
    )
)

# =========================================
# 3. 엣지 heat score 계산
# =========================================

edge_scores = []

for idx, edge in edges.iterrows():

    u = edge["u"]
    v = edge["v"]

    score_u = score_map.get(
        u,
        np.nan
    )

    score_v = score_map.get(
        v,
        np.nan
    )

    score = np.nanmean(
        [score_u, score_v]
    )

    edge_scores.append(score)

edges["heat_score"] = edge_scores

# =========================================
# 4. 분위수 계산
# =========================================

q1 = edges["heat_score"].quantile(0.2)
q2 = edges["heat_score"].quantile(0.4)
q3 = edges["heat_score"].quantile(0.6)
q4 = edges["heat_score"].quantile(0.8)

print()
print("===== 분위수 =====")
print(q1, q2, q3, q4)

# =========================================
# 5. 그래프 생성
# =========================================

G = nx.Graph()

# 노드 추가
for idx, row in nodes.iterrows():

    G.add_node(
        row["osmid"],
        x=row.geometry.x,
        y=row.geometry.y,
        heat_score=row["heat_score"]
    )

# =========================================
# 6. 엣지 추가
# 진짜 도로 geometry 유지
# =========================================

for idx, row in edges.iterrows():

    u = row["u"]
    v = row["v"]

    if u not in G.nodes:
        continue

    if v not in G.nodes:
        continue

    if row.geometry is None:
        continue

    edge_heat = row["heat_score"]

    if np.isnan(edge_heat):
        edge_heat = 999

    # =====================================
    # 핵심:
    # 더운 길에 매우 큰 패널티
    # =====================================

    # =====================================
    # Heat Score 기반 강한 패널티
    # =====================================

    if edge_heat <= q1:

        # 매우 시원
        multiplier = 0.3

    elif edge_heat <= q2:

        # 시원
        multiplier = 0.8

    elif edge_heat <= q3:

        # 보통
        multiplier = 2.5

    elif edge_heat <= q4:

        # 더움
        multiplier = 7

    else:

        # 매우 더움
        multiplier = 20

    # 최종 weight
    weight = (
            row["length"]
            * multiplier
    )

    G.add_edge(
        u,
        v,
        weight=weight,
        length=row["length"],
        heat_score=edge_heat,
        geometry=row.geometry
    )

print()
print("그래프 생성 완료")
print("총 노드:", G.number_of_nodes())
print("총 엣지:", G.number_of_edges())

# =========================================
# 7. 시원한 출발점 후보
# =========================================

cool_nodes = nodes[
    nodes["heat_score"] <= q2
]

start_candidates = (
    cool_nodes["osmid"]
    .sample(
        min(
            20,
            len(cool_nodes)
        ),
        random_state=random.randint(0, 99999)
    )
    .tolist()
)

# =========================================
# 8. 목표 거리
# =========================================

targets = {
    "1km": 1000,
    "3km": 3000,
    "5km": 5000
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
# 10. 경로 생성
# =========================================

for route_name, target_distance in targets.items():

    print()
    print("===== 생성 중 =====")
    print(route_name)

    route_found = False

    # 여러 출발점 시도
    for start_node in start_candidates:

        lengths = nx.single_source_dijkstra_path_length(
            G,
            start_node,
            weight="weight"
        )

        candidates = []

        for node_id, cost in lengths.items():

            try:

                real_distance = nx.shortest_path_length(
                    G,
                    start_node,
                    node_id,
                    weight="length"
                )

                diff = abs(
                    real_distance
                    - target_distance
                )

                candidates.append(
                    (
                        node_id,
                        real_distance,
                        diff
                    )
                )

            except:
                continue

        candidates.sort(
            key=lambda x: x[2]
        )

        if len(candidates) == 0:
            continue

        end_node = candidates[0][0]

        print("출발:", start_node)
        print("도착:", end_node)

        # =====================================
        # heat score 고려 경로
        # =====================================

        path = nx.shortest_path(
            G,
            source=start_node,
            target=end_node,
            weight="weight"
        )

        # =====================================
        # 지도 생성
        # =====================================

        m = folium.Map(
            location=[37.32, 127.09],
            zoom_start=13
        )

        # =====================================
        # 실제 edge geometry 사용
        # =====================================

        total_distance = 0

        for i in range(len(path) - 1):

            u = path[i]
            v = path[i + 1]

            if not G.has_edge(u, v):
                continue

            edge_data = G[u][v]

            geom = edge_data["geometry"]

            score = edge_data["heat_score"]

            color = get_color(score)

            total_distance += edge_data["length"]

            if geom.geom_type == "LineString":

                coords = [
                    [y, x]
                    for x, y in geom.coords
                ]

                folium.PolyLine(

                    locations=coords,

                    color=color,

                    weight=6,

                    opacity=0.95,

                    tooltip=(
                        f"""
                        Heat Score: {score:.2f}<br>
                        거리: {edge_data['length']:.1f}m
                        """
                    )

                ).add_to(m)

        # =====================================
        # 출발지
        # =====================================

        start_geom = nodes[
            nodes["osmid"] == start_node
        ].geometry.iloc[0]

        folium.Marker(

            location=[
                start_geom.y,
                start_geom.x
            ],

            tooltip="출발지",

            icon=folium.Icon(
                color="green"
            )

        ).add_to(m)

        # =====================================
        # 도착지
        # =====================================

        end_geom = nodes[
            nodes["osmid"] == end_node
        ].geometry.iloc[0]

        folium.Marker(

            location=[
                end_geom.y,
                end_geom.x
            ],

            tooltip="도착지",

            icon=folium.Icon(
                color="red"
            )

        ).add_to(m)

        # =====================================
        # 저장
        # =====================================

        output_path = (
            output_dir
            / f"cool_route_layer_{route_name}.html"
        )

        m.save(output_path)

        print(
            f"{route_name} 저장 완료"
        )

        print(
            f"실제 거리: {total_distance:.1f}m"
        )

        route_found = True
        break

    if not route_found:

        print(
            f"{route_name} 생성 실패"
        )
