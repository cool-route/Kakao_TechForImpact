import geopandas as gpd
import numpy as np

# 노드 읽기
nodes = gpd.read_file(
    "nodes_with_heat.geojson"
)

# 토지 데이터 읽기
land = gpd.read_file(
    r"C:\Users\kjenn\PyCharm_files\cool-route-data\data\land_sujigu_5186.geojson",
    encoding="utf-8"
)

# CRS 맞추기
land = land.to_crs(nodes.crs)

# 공간조인
joined = gpd.sjoin(
    nodes,
    land,
    how="left",
    predicate="intersects"
)

# 기본 shade
joined["shade"] = 0.2

# ------------------------
# 대분류 기반 shade 설정
# ------------------------

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

# ------------------------
# 결측값 처리
# ------------------------

joined["shade"] = joined["shade"].fillna(0.2)

print(
    joined[
        [
            "osmid",
            "lclsf_nm",
            "mclsf_nm",
            "shade"
        ]
    ].head()
)

# 저장
joined.to_file(
    "nodes_with_shade.geojson",
    driver="GeoJSON"
)

print("완료")