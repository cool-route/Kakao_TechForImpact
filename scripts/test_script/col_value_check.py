import geopandas as gpd

land = gpd.read_file(
    r"/data/land_sujigu_5186.geojson",
    encoding="cp949"
)

print(land.columns)

print()

print(land["lclsf_nm"].unique())

print()

print(land["mclsf_nm"].unique())