import geopandas as gpd

gdf = gpd.read_file(
    r"/data/output/nodes_with_utci.geojson"
)

# 더미 데이터
gdf["heat"] = 30
gdf["shade"] = 0.5

gdf["score"] = (
    0.5 * gdf["utci"]
    + 0.3 * gdf["heat"]
    - 0.2 * gdf["shade"]
)

print(gdf.head())

gdf.to_file(
    r"C:\Users\kjenn\PyCharm_files\cool-route-data\data\output\nodes_with_score.geojson",
    driver="GeoJSON"
)