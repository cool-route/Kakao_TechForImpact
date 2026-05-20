import geopandas as gpd

land = gpd.read_file(
    r"C:\Users\kjenn\PyCharm_files\cool-route-data\data\land_sujigu_5186.geojson",
    encoding="cp949"
)

print(land.columns)

print()

print(land["lclsf_nm"].unique())

print()

print(land["mclsf_nm"].unique())