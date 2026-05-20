import geopandas as gpd

gdf = gpd.read_file(
    r"C:\Users\kjenn\PyCharm_files\cool-route-data\data\land_sujigu.geojson"
)

print("변환 전:", gdf.crs)

gdf_5186 = gdf.to_crs(epsg=5186)

print("변환 후:", gdf_5186.crs)

gdf_5186.to_file(
    "land_sujigu_5186.geojson",
    driver="GeoJSON"
)