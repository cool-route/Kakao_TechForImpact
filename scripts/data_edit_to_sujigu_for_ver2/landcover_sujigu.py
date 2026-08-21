import geopandas as gpd

# 수지구 경계
boundary = gpd.read_file("data/sujigu_boundary.geojson")


# 토지이용 데이터
landcover = gpd.read_file(
    "data\\raw\\토지이용_토지피복지도_용인시_20251021\\biotop_lndcvg_41460_20251021.shp"
)

# 수지구 경계의 좌표계를 토지이용 데이터와 동일하게 변경
boundary = boundary.to_crs(landcover.crs)

print("===== 수지구 =====")
print("CRS:", boundary.crs)
print("개수:", len(boundary))

print()
print("===== 토지이용 =====")
print("CRS:", landcover.crs)
print("개수:", len(landcover))
print("컬럼:", landcover.columns.tolist())

landcover_suji = gpd.clip(landcover, boundary)

print("수지구 토지이용:", len(landcover_suji))

landcover_suji.to_file(
    "data/processed_data/토지이용_토지피복도_수지구/landcover_suji.shp",
    encoding="utf-8"
)

print("토지이용 데이터 저장 완료!")