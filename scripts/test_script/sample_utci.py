from pathlib import Path
import geopandas as gpd
import rasterio

# 프로젝트 기준 경로
BASE_DIR = Path(__file__).resolve().parent.parent

nodes = gpd.read_file(
    BASE_DIR / "data" / "sujiku_nodes_5186.geojson"
)

with rasterio.open(
    BASE_DIR / "data" / "sujigu_felt_temp.tif"
) as src:

    values = []

    for point in nodes.geometry:

        x = point.x
        y = point.y

        row, col = src.index(x, y)

        value = src.read(1)[row, col]

        values.append(value)

nodes["utci"] = values

print(nodes.head())

nodes.to_file(
    BASE_DIR / "data" / "output" / "nodes_with_utci.geojson",
    driver="GeoJSON"
)