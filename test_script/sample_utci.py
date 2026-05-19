import geopandas as gpd
import rasterio

nodes = gpd.read_file(
    r"C:\Users\kjenn\PyCharm_files\cool-route-data\sujiku_nodes_5186.geojson"
)

with rasterio.open(
    r"C:\Users\kjenn\PyCharm_files\cool-route-data\data\sujigu_felt_temp.tif"
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
    r"C:\Users\kjenn\PyCharm_files\cool-route-data\data\nodes_with_utci.geojson",
    driver="GeoJSON"
)