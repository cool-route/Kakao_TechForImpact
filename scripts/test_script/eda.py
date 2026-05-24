from pathlib import Path
import geopandas as gpd

# 프로젝트 기준 경로
BASE_DIR = Path(__file__).resolve().parent.parent

gdf = gpd.read_file(
    BASE_DIR
    / "data"
    / "output"
    / "nodes_with_utci.geojson"
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