from pathlib import Path

import geopandas as gpd
import numpy as np

# =========================================
# 경로 설정
# =========================================

BASE_DIR = Path(__file__).resolve().parent.parent

nodes_path = (
    BASE_DIR
    / "data"
    / "nodes_with_heat.geojson"
)

land_path = (
    BASE_DIR
    / "data"
    / "land_sujigu_5186.geojson"
)

output_path = (
    BASE_DIR
    / "data"
    / "nodes_with_shade.geojson"
)

# =========================================
# 노드 읽기
# =========================================

nodes = gpd.read_file(nodes_path)

# =========================================
# 토지 데이터 읽기
# =========================================

land = gpd.read_file(
    land_path,
    encoding="utf-8"
)

# =========================================
# CRS 맞추기
# =========================================

land = land.to_crs(nodes.crs)

# =========================================
# 공간조인
# =========================================

joined = gpd.sjoin(
    nodes,
    land,
    how="left",
    predicate="intersects"
)

# =========================================
# 기본 shade
# =========================================

joined["shade"] = 0.2

# =========================================
# 대분류 기반 shade 설정
# =========================================

# 조성녹지
joined.loc[
    joined["lclsf_nm"] == "조성녹지",
    "shade"
] = 0.8

# 산림
joined.loc[
    joined["lclsf_nm"] == "산림",
    "shade"
] = 1.0

# 초지
joined.loc[
    joined["ldc_lc_nm"] == "초지",
    "shade"
] = 0.5

# 도로녹지
joined.loc[
    joined["mclsf_nm"] == "도로녹지",
    "shade"
] = 0.7

# =========================================
# 결측값 처리
# =========================================

joined["shade"] = (
    joined["shade"]
    .fillna(0.2)
)

# =========================================
# 필요한 컬럼만 유지
# =========================================

keep_columns = [
    "osmid",
    "felt_temp",
    "heat_grade",
    "shade",
    "geometry"
]

joined = joined[keep_columns]

# =========================================
# 확인 출력
# =========================================

print(
    joined[
        [
            "osmid",
            "shade"
        ]
    ].head()
)

print()

print("shade 통계:")

print(
    joined["shade"]
    .describe()
)

# =========================================
# 저장
# =========================================

joined.to_file(
    output_path,
    driver="GeoJSON"
)

print()
print("완료!")
print(output_path)