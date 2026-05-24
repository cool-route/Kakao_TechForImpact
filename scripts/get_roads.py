from pathlib import Path

import osmnx as ox
import geopandas as gpd

# =========================================
# 경로 설정
# =========================================

BASE_DIR = Path(__file__).resolve().parent.parent

nodes_output = (
    BASE_DIR
    / "data"
    / "sujiku_nodes_5186.geojson"
)

edges_output = (
    BASE_DIR
    / "data"
    / "sujiku_edges_5186.geojson"
)

# =========================================
# 지역 설정
# =========================================

place_name = "Suji-gu, Yongin-si, South Korea"

# =========================================
# 그래프 가져오기
# =========================================

G = ox.graph_from_place(
    place_name,
    network_type="drive"
)

# =========================================
# GeoDataFrame 변환
# =========================================

nodes, edges = ox.graph_to_gdfs(G)

# =========================================
# MultiIndex → 컬럼화
# =========================================

edges = edges.reset_index()

nodes = nodes.reset_index()

# =========================================
# CRS 변환
# EPSG:5186
# =========================================

nodes = nodes.to_crs(epsg=5186)

edges = edges.to_crs(epsg=5186)

# =========================================
# 확인 출력
# =========================================

print()

print("노드 개수:")
print(len(nodes))

print()

print("엣지 개수:")
print(len(edges))

print()

print("노드 CRS:")
print(nodes.crs)

print()

print("엣지 CRS:")
print(edges.crs)

# =========================================
# 저장
# =========================================

nodes.to_file(
    nodes_output,
    driver="GeoJSON"
)

edges.to_file(
    edges_output,
    driver="GeoJSON"
)

print()

print("완료!")
print(nodes_output)
print(edges_output)