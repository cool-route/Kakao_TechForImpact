from pathlib import Path
import geopandas as gpd

# 프로젝트 기준 경로
BASE_DIR = Path(__file__).resolve().parent.parent

gdf = gpd.read_file(
    BASE_DIR / "data" / "land_sujigu.geojson"
)

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