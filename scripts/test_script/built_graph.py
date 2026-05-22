import geopandas as gpd
import networkx as nx
import numpy as np

# =====================================
# 1. 파일 읽기
# =====================================

nodes = gpd.read_file(
    "../data/nodes_with_score.geojson"
)

edges = gpd.read_file(
    "../data/sujiku_edges_5186.geojson"
)

# =====================================
# 2. 그래프 생성
# =====================================

G = nx.Graph()

# =====================================
# 3. 노드 추가
# =====================================

for idx, row in nodes.iterrows():

    G.add_node(
        row["osmid"],
        x=row.geometry.x,
        y=row.geometry.y,
        heat_score=row["heat_score"]
    )

# =====================================
# 4. 엣지 추가
# =====================================

for idx, row in edges.iterrows():

    try:
        u = row["u"]
        v = row["v"]

        # 노드 heat score
        score_u = G.nodes[u]["heat_score"]
        score_v = G.nodes[v]["heat_score"]

        avg_score = (
            score_u + score_v
        ) / 2

        # 도로 길이
        length = row["length"]

        # 핵심:
        # 시원한 길 우선 weight
        weight = (
            length
            *
            (1 + avg_score * 0.05)
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

print()
print("그래프 생성 완료")
print("노드 수:", G.number_of_nodes())
print("엣지 수:", G.number_of_edges())