from pathlib import Path

import geopandas as gpd
import rasterio
import numpy as np

# =========================================
# 경로 설정
# =========================================

BASE_DIR = Path(__file__).resolve().parent.parent

nodes_path = (
    BASE_DIR
    / "data"
    / "nodes_with_felt_temp.geojson"
)

tif_path = (
    BASE_DIR
    / "data"
    / "sujigu_heat_grade.tif"
)

output_path = (
    BASE_DIR
    / "data"
    / "nodes_with_heat.geojson"
)

# =========================================
# 노드 읽기
# =========================================

nodes = gpd.read_file(nodes_path)

# =========================================
# tif 열기
# =========================================

with rasterio.open(tif_path) as src:

    band = src.read(1)

    grades = []

    for point in nodes.geometry:

        x = point.x
        y = point.y

        row, col = src.index(x, y)

        if (
            0 <= row < src.height
            and
            0 <= col < src.width
        ):

            value = band[row, col]

            # nodata 처리
            if value == src.nodata:
                value = np.nan

        else:
            value = np.nan

        grades.append(value)

# =========================================
# 컬럼 추가
# =========================================

nodes["heat_grade"] = grades

# =========================================
# 확인 출력
# =========================================

print(
    nodes[
        [
            "osmid",
            "felt_temp",
            "heat_grade"
        ]
    ].head()
)

print()

print("heat_grade 결측값 개수:")

print(
    nodes["heat_grade"]
    .isna()
    .sum()
)

# =========================================
# 저장
# =========================================

nodes.to_file(
    output_path,
    driver="GeoJSON"
)

print()
print("저장 완료!")
print(output_path)