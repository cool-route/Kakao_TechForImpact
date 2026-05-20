import geopandas as gpd

gdf = gpd.read_file(r"/data/land_sujigu.geojson")

print(gdf.head())
print()

print("컬럼:")
print(gdf.columns)
print()

print("좌표계:")
print(gdf.crs)
print()

print("geometry 타입:")
print(gdf.geom_type.unique())