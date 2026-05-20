import rasterio
from rasterio.crs import CRS

path = r"C:\Users\kjenn\PyCharm_files\cool-route-data\data\sujigu_heat_grade.tif"

with rasterio.open(path, "r+") as src:
    src.crs = CRS.from_epsg(5186)

print("CRS 지정 완료")