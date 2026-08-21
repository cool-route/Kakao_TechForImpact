import rasterio
import geopandas as gpd
from rasterio.mask import mask

slope_path = "data/raw/경사도 15도 이상_용인시_20251021/rst_slope_15_ovr_41460_20251021.tif"

with rasterio.open(slope_path) as src:
    print("===== 경사도 TIF =====")
    print("CRS:", src.crs)
    print("너비:", src.width)
    print("높이:", src.height)
    print("밴드 수:", src.count)
    print("데이터 타입:", src.dtypes)
    print("NoData:", src.nodata)
    print("Bounds:", src.bounds)
    

# =========================
# 1. 수지구 경계 읽기
# =========================
boundary = gpd.read_file(
    "data/sujigu_boundary.geojson"
)

print("원래 수지구 CRS:", boundary.crs)


with rasterio.open(slope_path) as src:

    print("TIF CRS:", src.crs)

    # =========================
    # 3. 수지구 경계를 TIF CRS로 변환
    # =========================
    boundary_slope = boundary.to_crs(src.crs)

    print(
        "변환된 수지구 CRS:",
        boundary_slope.crs
    )

    # =========================
    # 4. GeoJSON geometry 추출
    # =========================
    geometries = boundary_slope.geometry

    # =========================
    # 5. 수지구 영역으로 TIF 자르기
    # =========================
    out_image, out_transform = mask(
        src,
        geometries,
        crop=True
    )

    # =========================
    # 6. 기존 TIF 메타데이터 가져오기
    # =========================
    out_meta = src.meta.copy()

    # 크기 변경
    out_meta.update({
        "height": out_image.shape[1],
        "width": out_image.shape[2],
        "transform": out_transform
    })


# =========================
# 7. 결과 저장
# =========================
output_path = (
    "data/processed_data/경사도 15도 이상_수지구/slope_15_suji.tif"
)

with rasterio.open(
    output_path,
    "w",
    **out_meta
) as dest:

    dest.write(out_image)


print()
print("===== 완료 =====")
print("저장 위치:", output_path)
print("출력 크기:", out_image.shape)