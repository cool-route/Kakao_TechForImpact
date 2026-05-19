import osmnx as ox
import geopandas as gpd

# 1. 지역 이름 설정
place_name = "Suji-gu, Yongin-si, South Korea"

# 2. 도로 네트워크 가져오기
G = ox.graph_from_place(
    place_name,
    network_type="drive"
)

# 3. 노드/엣지로 변환
nodes, edges = ox.graph_to_gdfs(G)

# ⭐ EPSG:5186으로 변환
nodes = nodes.to_crs(epsg=5186)
edges = edges.to_crs(epsg=5186)

# 4. 저장
nodes.to_file(
    "sujiku_nodes_5186.geojson",
    driver="GeoJSON"
)

edges.to_file(
    "sujiku_edges_5186.geojson",
    driver="GeoJSON"
)

print("완료!")

# 확인
print(nodes.crs)
print(edges.crs)

print(nodes.head())