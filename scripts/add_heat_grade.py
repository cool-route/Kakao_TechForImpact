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

print("노드 개수:", len(nodes))
print("엣지 개수:", len(edges))

# =====================================
# 그래프 생성
# =====================================

G = nx.Graph()

# =====================================
# 노드 추가
# =====================================

for idx, row in nodes.iterrows():

    G.add_node(
        row["osmid"],

        x=row.geometry.x,
        y=row.geometry.y,

        heat_score=row["heat_score"]
    )

# =====================================
# 엣지 추가
# =====================================

for idx, row in edges.iterrows():

    try:

        u = row["u"]
        v = row["v"]

        # 길이
        length = row.get(
            "length",
            1
        )

        # 양 끝 노드 score 평균
        score_u = G.nodes[u]["heat_score"]
        score_v = G.nodes[v]["heat_score"]

        avg_score = (
            score_u + score_v
        ) / 2

        # -------------------------
        # 핵심 weight
        # -------------------------
        #
        # 길이가 짧고
        # heat_score 낮을수록 유리
        #
        # -------------------------

        weight = (
            length
            *
            (1 + avg_score)
        )

        G.add_edge(
            u,
            v,

            weight=weight,
            length=length,

            heat_score=avg_score,

            geometry=row.geometry
        )

    except:
        continue

# =====================================
# 완료 출력
# =====================================

print()
print("그래프 생성 완료")

print(
    "총 노드:",
    G.number_of_nodes()
)

print(
    "총 엣지:",
    G.number_of_edges()
)