from pathlib import Path
import geopandas as gpd

# 프로젝트 기준 경로
BASE_DIR = Path(__file__).resolve().parent.parent

land = gpd.read_file(
    BASE_DIR / "data" / "land_sujigu_5186.geojson",
    encoding="cp949"
)

print(land.columns)

print()

print(land["lclsf_nm"].unique())

print()

print(land["mclsf_nm"].unique())