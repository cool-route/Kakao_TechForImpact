import geopandas as gpd

boundary = gpd.read_file("data/sujigu_boundary.geojson")

print(boundary)
print("CRS:", boundary.crs)
print("개수:", len(boundary))
print("컬럼:", boundary.columns.tolist())