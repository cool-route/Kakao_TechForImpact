import geopandas as gpd

# 수지구 경계
boundary = gpd.read_file("data/sujigu_boundary.geojson")

# 녹지 현황도
green = gpd.read_file(
    "data\\raw\\녹지 현황도_용인시_20251021\\grbt_41460_20251021.shp"
)

# 수지구 경계의 좌표계를 녹지 데이터와 동일하게 변경
boundary = boundary.to_crs(green.crs)

print("===== 수지구 =====")
print("CRS:", boundary.crs)
print("개수:", len(boundary))

print()
print("===== 녹지 =====")
print("CRS:", green.crs)
print("개수:", len(green))
print("컬럼:", green.columns.tolist())

green_suji = gpd.clip(green, boundary)

print("수지구 녹지 개수:", len(green_suji))

green_suji.to_file(
    "data/processed_data/green_suji.shp",
    encoding="utf-8"
)

print("녹지 데이터 저장 완료!")