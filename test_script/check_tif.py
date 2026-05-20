import rasterio
import matplotlib.pyplot as plt

# path = r"C:\Users\kjenn\PyCharm_files\cool-route-data\data\sujigu_felt_temp.tif"
path = r"C:\Users\kjenn\PyCharm_files\cool-route-data\data\sujigu_heat_grade.tif"

with rasterio.open(path) as src:
    print("좌표계:", src.crs)
    print("너비:", src.width)
    print("높이:", src.height)
    print("밴드 수:", src.count)
    print("nodata:", src.nodata)
    print("bounds:", src.bounds)

    data = src.read(1)

plt.imshow(data)
plt.colorbar()
plt.title("UTCI Raster")
plt.show()