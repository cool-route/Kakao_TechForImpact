import geopandas as gpd
import rasterio
import numpy as np

nodes = gpd.read_file(
    "nodes_with_felt_temp.geojson"
)

with rasterio.open(
        r"/data/sujigu_heat_grade.tif"
) as src:

    band = src.read(1)

    grades = []

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

            if value == src.nodata:
                value = np.nan

        else:
            value = np.nan

        grades.append(value)

nodes["heat_grade"] = grades

print(
    nodes[
        ["osmid", "felt_temp", "heat_grade"]
    ].head()
)

nodes.to_file(
    "nodes_with_heat.geojson",
    driver="GeoJSON"
)