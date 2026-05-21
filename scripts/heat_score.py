from pathlib import Path

import geopandas as gpd

# =========================================
# 경로 설정
# =========================================

BASE_DIR = Path(__file__).resolve().parent.parent

input_path = (
    BASE_DIR
    / "data"
    / "output"
    / "nodes_with_utci.geojson"
)

output_path = (
    BASE_DIR
    / "data"
    / "output"
    / "nodes_with_score.geojson"
)

# =========================================
# 파일 읽기
# =========================================

gdf = gpd.read_file(input_path)

# =========================================
# 더미 데이터
# =========================================

gdf["heat"] = 30

gdf["shade"] = 0.5

# =========================================
# Score 계산
# =========================================

gdf["score"] = (

    0.5 * gdf["utci"]

    +

    0.3 * gdf["heat"]

    -

    0.2 * gdf["shade"]

)

# =========================================
# 출력 확인
# =========================================

print(
    gdf[
        [
            "utci",
            "heat",
            "shade",
            "score"
        ]
    ].head()
)

print()

print("score 통계:")

print(
    gdf["score"]
    .describe()
)

# =========================================
# 저장
# =========================================

gdf.to_file(
    output_path,
    driver="GeoJSON"
)

print()

print("저장 완료!")
print(output_path)