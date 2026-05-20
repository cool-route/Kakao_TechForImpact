import geopandas as gpd

gdf = gpd.read_file(
    r"../data/output/nodes_with_utci.geojson"
)

print(gdf["utci"].describe())

print()

print("결측값:")
print(gdf["utci"].isna().sum())

print()

print("최대값:")
print(gdf["utci"].max())

print()

print("최소값:")
print(gdf["utci"].min())