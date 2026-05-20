import geopandas as gpd
import numpy as np
import json

# ====================================
# 1. presets 불러오기
# ====================================

with open("presets.json", "r", encoding="utf-8") as f:
    presets = json.load(f)

# 현재 사용할 모드
MODE = "elderly"

p = presets[MODE]

# ====================================
# 2. 파일 읽기
# ====================================

nodes = gpd.read_file(
    "nodes_with_shade.geojson"
)

# ====================================
# 3. 결측값 처리
# ====================================

nodes["felt_temp"] = (
    nodes["felt_temp"]
    .fillna(
        nodes["felt_temp"].mean()
    )
)

nodes["heat_grade"] = (
    nodes["heat_grade"]
    .fillna(
        nodes["heat_grade"].mean()
    )
)

nodes["shade"] = (
    nodes["shade"]
    .fillna(0.2)
)

# ====================================
# 4. preset 기반 Heat Score 계산
# ====================================

nodes["heat_score"] = (
    p["felt_temp_weight"]
    *
    nodes["felt_temp"]

    +

    p["heat_grade_weight"]
    *
    nodes["heat_grade"]

    -

    p["shade_weight"]
    *
    nodes["shade"]
)

# ====================================
# 5. 반올림
# ====================================

nodes["heat_score"] = (
    nodes["heat_score"]
    .round(2)
)

# ====================================
# 6. 출력 확인
# ====================================

print()

print("현재 모드:", MODE)

print()

print(
    nodes[
        [
            "felt_temp",
            "heat_grade",
            "shade",
            "heat_score"
        ]
    ].head()
)

print()

print("Heat Score 통계")

print(
    nodes["heat_score"].describe()
)

# ====================================
# 7. 저장 ⭐⭐⭐
# ====================================

nodes.to_file(
    "nodes_with_score.geojson",
    driver="GeoJSON"
)

print()

print("nodes_with_score.geojson 저장 완료")