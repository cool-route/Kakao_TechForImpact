from pathlib import Path

import geopandas as gpd
import networkx as nx
import folium
import random
import numpy as np

# =========================================
# 0. 경로 설정
# =========================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

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
# 1. 파일 읽기
# =========================================

nodes = gpd.read_file(nodes_path)
edges = gpd.read_file(edges_path)

# =========================================
# 2. heat score dictionary
# =========================================

score_map = dict(
    zip(
        nodes["osmid"],
        nodes["heat_score"]
    )
)

# =========================================
# 3. 그래프 생성
# "시원한 길 우선" weight 적용
# =========================================

G = nx.Graph()

for idx, row in edges.iterrows():

    try:

        u = row["u"]
        v = row["v"]

        length = row["length"]

        score_u = score_map.get(u, np.nan)
        score_v = score_map.get(v, np.nan)

        edge_score = np.nanmean(
            [score_u, score_v]
        )

        # ---------------------------------
        # 핵심!!!
        # 더운 길일수록 cost 증가
        # ---------------------------------

        # =====================================
        # 시원한 길 강력 우선
        # =====================================

        cool_threshold = 19

        heat_penalty = max(
            0,
            edge_score - cool_threshold
        )

        cool_weight = (

                length

                +

                (heat_penalty ** 2) * 80

        )

        G.add_edge(

            u,
            v,

            weight=cool_weight,

            length=length,

            heat_score=edge_score,

            geometry=row.geometry

        )

    except:
        continue

print()
print("그래프 생성 완료")
print("노드:", G.number_of_nodes())
print("엣지:", G.number_of_edges())

# =========================================
# 4. 시원한 노드 중 랜덤 출발지
# =========================================

cool_nodes = nodes[
    nodes["heat_score"]
    <=
    nodes["heat_score"].quantile(0.3)
]

start_row = cool_nodes.sample(1).iloc[0]

start_node = start_row["osmid"]

print()
print("출발 노드:", start_node)

# =========================================
# 5. 목표 거리
# =========================================

targets = {
    "1km": 1000,
    "3km": 3000,
    "5km": 5000
}

# =========================================
# 6. heat 분위수
# =========================================

all_scores = []

for u, v, data in G.edges(data=True):

    score = data["heat_score"]

    if not np.isnan(score):
        all_scores.append(score)

q1 = np.quantile(all_scores, 0.2)
q2 = np.quantile(all_scores, 0.4)
q3 = np.quantile(all_scores, 0.6)
q4 = np.quantile(all_scores, 0.8)

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
# 8. 거리별 경로 생성
# =========================================

for label, target_dist in targets.items():

    print()
    print("==========")
    print(label)

    # ---------------------------------
    # 실제 거리 기준 탐색
    # ---------------------------------

    real_lengths = nx.single_source_dijkstra_path_length(
        G,
        start_node,
        weight="length"
    )

    # 목표 거리 근처 노드 찾기
    best_node = None
    best_diff = 999999999

    for node_id, dist in real_lengths.items():

        diff = abs(dist - target_dist)

        if diff < best_diff:

            best_diff = diff
            best_node = node_id

    print("도착 노드:", best_node)

    # =====================================
    # 시원한 길 우선 shortest path
    # =====================================

    path = nx.shortest_path(

        G,

        source=start_node,

        target=best_node,

        weight="weight"

    )

    print("경로 노드 수:", len(path))

    # =====================================
    # 지도 생성
    # =====================================

    m = folium.Map(
        location=[37.32, 127.09],
        zoom_start=13
    )

    # =====================================
    # 경로 시각화
    # =====================================

    total_real_dist = 0

    for i in range(len(path) - 1):

        u = path[i]
        v = path[i + 1]

        if not G.has_edge(u, v):
            continue

        edge_data = G[u][v]

        geom = edge_data["geometry"]

        score = edge_data["heat_score"]

        total_real_dist += edge_data["length"]

        color = get_color(score)

        # -----------------------------
        # geometry 좌표 변환
        # -----------------------------

        geom_4326 = gpd.GeoSeries(
            [geom],
            crs="EPSG:5186"
        ).to_crs(epsg=4326)

        line = geom_4326.iloc[0]

        coords = [
            [y, x]
            for x, y in line.coords
        ]

        folium.PolyLine(

            locations=coords,

            color=color,

            weight=6,

            opacity=0.9,

            tooltip=(
                f"""
                Heat Score: {score:.2f}<br>
                Length: {edge_data['length']:.1f}m
                """
            )

        ).add_to(m)

    # =====================================
    # 출발지
    # =====================================

    start_geom = nodes[
        nodes["osmid"] == start_node
    ].to_crs(epsg=4326).iloc[0].geometry

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
        nodes["osmid"] == best_node
    ].to_crs(epsg=4326).iloc[0].geometry

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
    # 제목 표시
    # =====================================

    title_html = f"""
    <h3 align="center">
    <b>
    {label} 시원한 경로
    <br>
    실제 거리:
    {total_real_dist:.1f}m
    </b>
    </h3>
    """

    m.get_root().html.add_child(
        folium.Element(title_html)
    )

    # =====================================
    # 저장
    # =====================================

    output_file = (
        output_dir
        / f"cool_route_{label}.html"
    )

    m.save(output_file)

    print()
    print(f"{output_file.name} 저장 완료")