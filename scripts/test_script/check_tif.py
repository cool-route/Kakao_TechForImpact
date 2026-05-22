from pathlib import Path
import rasterio
import matplotlib.pyplot as plt

# 프로젝트 기준 경로
BASE_DIR = Path(__file__).resolve().parent.parent

# path = BASE_DIR / "data" / "sujigu_felt_temp.tif"

path = (
    BASE_DIR
    / "data"
    / "sujigu_heat_grade.tif"
)

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