import geopandas as gpd
import rasterio
from rasterio.mask import mask


# =========================
# 1. 수지구 경계 읽기
# =========================
boundary = gpd.read_file(
    "data/sujigu_boundary.geojson"
)

print("원래 수지구 CRS:", boundary.crs)


# =========================
# 2. 폭염 시 더위 강도 지도 TIF 열기
# =========================
ctyart_path = (
    "data/raw/폭염 시 더위 강도 지도_용인시_20260722/rst_ctyart_41460.tif"
)

with rasterio.open(ctyart_path) as src:

    print("TIF CRS:", src.crs)
    print("원본 크기:", src.width, "x", src.height)
    print("NoData:", src.nodata)

    # =========================
    # 3. 수지구 경계를 TIF CRS로 변환
    # =========================
    boundary_uhtln = boundary.to_crs(src.crs)

    print(
        "변환된 수지구 CRS:",
        boundary_uhtln.crs
    )

    # =========================
    # 4. 수지구 geometry 추출
    # =========================
    geometries = boundary_uhtln.geometry

    # =========================
    # 5. 수지구 영역으로 TIF 자르기
    # =========================
    out_image, out_transform = mask(
        src,
        geometries,
        crop=True
    )

    # =========================
    # 6. 기존 TIF 메타데이터 복사
    # =========================
    out_meta = src.meta.copy()

    out_meta.update({
        "height": out_image.shape[1],
        "width": out_image.shape[2],
        "transform": out_transform
    })


# =========================
# 7. 결과 저장
# =========================
output_path = (
    "data/processed_data/폭염시_더위_강도_지도_수지구/ctyart_suji.tif"
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