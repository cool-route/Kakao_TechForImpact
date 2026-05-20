import osmnx as ox
import geopandas as gpd

# 지역
place_name = "Suji-gu, Yongin-si, South Korea"

# 그래프 가져오기
G = ox.graph_from_place(
    place_name,
    network_type="drive"
)

# GeoDataFrame 변환
nodes, edges = ox.graph_to_gdfs(G)

# ⭐ 중요
# MultiIndex → 컬럼화
edges = edges.reset_index()

nodes = nodes.reset_index()

# CRS 변환
nodes = nodes.to_crs(epsg=5186)
edges = edges.to_crs(epsg=5186)

# 저장
nodes.to_file(
    "sujiku_nodes_5186.geojson",
    driver="GeoJSON"
)

edges.to_file(
    "sujiku_edges_5186.geojson",
    driver="GeoJSON"
)

print("완료")