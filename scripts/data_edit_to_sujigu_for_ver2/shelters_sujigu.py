import geopandas as gpd

# 수지구 경계
boundary = gpd.read_file("data/sujigu_boundary.geojson")

# 무더위 쉼터
shelters = gpd.read_file(
    "data\\raw\\무더위쉼터_용인시_20260722\\swtr_rstar_41460_20260722.shp"
)

# 수지구 경계의 좌표계를 무더위 쉼터 데이터와 동일하게 변경
boundary = boundary.to_crs(shelters.crs)

print("===== 수지구 =====")
print("CRS:", boundary.crs)
print("개수:", len(boundary))

print()
print("===== 무더위 쉼터 =====")
print("CRS:", shelters.crs)
print("개수:", len(shelters))
print("컬럼:", shelters.columns.tolist())

shelters_suji = gpd.clip(shelters, boundary)

print("수지구 무더위 쉼터 개수:", len(shelters_suji))

shelters_suji.to_file(
    "data/processed_data/shelters_suji.shp",
    encoding="utf-8"
)

print("무더위 쉼터 데이터 저장 완료!")