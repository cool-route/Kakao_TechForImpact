import geopandas as gpd
import rasterio
import numpy as np

# 노드 읽기
nodes = gpd.read_file(
    r"/scripts/sujiku_nodes_5186.geojson"
)

# tif 열기
with rasterio.open(
        r"/data/sujigu_felt_temp.tif"
) as src:

    band = src.read(1)

    values = []

    for point in nodes.geometry:

        x = point.x
        y = point.y

        row, col = src.index(x, y)

        if (
            0 <= row < src.height
            and
            0 <= col < src.width
        ):
            value = band[row, col]

            # nodata 처리
            if value == src.nodata:
                value = np.nan

        else:
            value = np.nan

        values.append(value)

nodes["felt_temp"] = values

print(nodes[["osmid", "felt_temp"]].head())

nodes.to_file(
    "nodes_with_felt_temp.geojson",
    driver="GeoJSON"
)