import geopandas as gpd

# =========================
# 1. 수지구 경계
# =========================
boundary = gpd.read_file("data/sujigu_boundary.geojson")

print("===== 수지구 =====")
print("CRS:", boundary.crs)
print("개수:", len(boundary))


# =========================
# 2. 비오톱 유형도
# =========================
biotop = gpd.read_file(
    "data/raw/녹지 현황도_용인시_20251021/grbt_41460_20251021.shp"
)

print()
print("===== 비오톱 =====")
print("CRS:", biotop.crs)
print("개수:", len(biotop))
print("컬럼:", biotop.columns.tolist())


# =========================
# 3. 좌표계 맞추기
# =========================
boundary_biotop = boundary.to_crs(biotop.crs)

print()
print("===== 좌표계 변환 후 =====")
print("수지구 CRS:", boundary_biotop.crs)
print("비오톱 CRS:", biotop.crs)


# =========================
# 4. 수지구 영역만 잘라내기
# =========================
biotop_suji = gpd.clip(
    biotop,
    boundary_biotop
)

print()
print("===== 필터링 결과 =====")
print("수지구 비오톱 개수:", len(biotop_suji))


# =========================
# 5. 결과 저장
# =========================
biotop_suji.to_file(
    "data/processed_data/비오톱 유형도_수지구/biotop_suji.shp",
    encoding="utf-8"
)

print("비오톱 데이터 저장 완료!")