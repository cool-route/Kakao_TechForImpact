import geopandas as gpd
import networkx as nx

from pathlib import Path

# =====================================
# 경로 설정
# =====================================

BASE_DIR = (
    Path(__file__).resolve().parent.parent
)

DATA_DIR = BASE_DIR / "data"

# =====================================
# 파일 읽기
# =====================================

nodes = gpd.read_file(
    DATA_DIR / "nodes_with_score.geojson"
)

edges = gpd.read_file(
    DATA_DIR / "sujiku_edges_5186.geojson"
)

# =====================================
# 그래프 생성
# =====================================

G = nx.Graph()

# 노드 추가
for idx, row in nodes.iterrows():

    G.add_node(
        row["osmid"],

        x=row.geometry.x,
        y=row.geometry.y,

        heat_score=row["heat_score"]
    )

# 엣지 추가
for idx, row in edges.iterrows():

    try:

        u = row["u"]
        v = row["v"]

        length = row.get(
            "length",
            1
        )

        score_u = G.nodes[u]["heat_score"]
        score_v = G.nodes[v]["heat_score"]

        avg_score = (
            score_u + score_v
        ) / 2

        weight = (
            length
            *
            (1 + avg_score)
        )

        G.add_edge(
            u,
            v,

            weight=weight,
            length=length
        )

    except:
        continue

# =====================================
# 출발 노드 선택
# =====================================

# 첫 번째 노드 사용
start_node = list(G.nodes)[0]

print()
print("출발 노드:")
print(start_node)

# =====================================
# 거리 계산
# length 기준 최단거리
# =====================================

distances = nx.single_source_dijkstra_path_length(
    G,
    start_node,
    weight="length"
)

# =====================================
# 목표 거리 찾기 함수
# =====================================

def find_near_distance_node(
        target_distance,
        tolerance=100
):

    candidates = []

    for node, dist in distances.items():

        if (
            target_distance - tolerance
            <= dist
            <= target_distance + tolerance
        ):

            candidates.append(
                (node, dist)
            )

    return candidates

# =====================================
# 후보 찾기
# =====================================

targets_1km = find_near_distance_node(1000)

targets_3km = find_near_distance_node(3000)

targets_5km = find_near_distance_node(5000)

# =====================================
# 출력
# =====================================

print()
print("===== 1km 후보 =====")

for node, dist in targets_1km[:5]:

    print(node, round(dist, 1))

print()
print("===== 3km 후보 =====")

for node, dist in targets_3km[:5]:

    print(node, round(dist, 1))

print()
print("===== 5km 후보 =====")

for node, dist in targets_5km[:5]:

    print(node, round(dist, 1))