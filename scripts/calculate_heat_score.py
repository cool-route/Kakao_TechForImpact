from pathlib import Path

import geopandas as gpd
import numpy as np
import json

# ====================================
# 경로 설정
# ====================================

BASE_DIR = Path(__file__).resolve().parent.parent

preset_path = (
    BASE_DIR
    / "data"
    / "presets.json"
)

nodes_path = (
    BASE_DIR
    / "data"
    / "nodes_with_shade.geojson"
)

output_path = (
    BASE_DIR
    / "data"
    / "nodes_with_score.geojson"
)

# ====================================
# 1. presets 불러오기
# ====================================

with open(
    preset_path,
    "r",
    encoding="utf-8"
) as f:

    presets = json.load(f)

# 현재 사용할 모드
MODE = "elderly"

p = presets[MODE]

# ====================================
# 2. 파일 읽기
# ====================================

nodes = gpd.read_file(nodes_path)

print()
print("노드 개수:", len(nodes))

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
# 4. heat_grade 정규화
# ====================================

# heat_grade 범위 확인
heat_min = nodes["heat_grade"].min()
heat_max = nodes["heat_grade"].max()

print()
print("heat_grade 최소:", heat_min)
print("heat_grade 최대:", heat_max)

# Min-Max Normalization
# 0 ~ 1 범위로 변환

nodes["heat_grade_norm"] = (

    (
        nodes["heat_grade"]
        -
        heat_min
    )

    /

    (
        heat_max
        -
        heat_min
    )

)

# ====================================
# 5. preset 기반 Heat Score 계산
# ====================================

# 핵심:
# felt_temp는 실제 온도
# heat_grade는 상대 열 취약도
# shade는 시원함 보정

nodes["heat_score"] = (

    # 체감온도
    p["felt_temp_weight"]
    *
    nodes["felt_temp"]

    +

    # 열취약도 가중치
    p["heat_grade_weight"]
    *
    (
        nodes["heat_grade_norm"]
        * 5
    )

    -

    # shade 보정
    p["shade_weight"]
    *
    (
        nodes["shade"]
        * 3
    )

)

# ====================================
# 6. 반올림
# ====================================

nodes["heat_score"] = (
    nodes["heat_score"]
    .round(2)
)

nodes["heat_grade_norm"] = (
    nodes["heat_grade_norm"]
    .round(3)
)

# ====================================
# 7. 출력 확인
# ====================================

print()

print("현재 모드:", MODE)

print()

print(
    nodes[
        [
            "felt_temp",
            "heat_grade",
            "heat_grade_norm",
            "shade",
            "heat_score"
        ]
    ].head(10)
)

print()

print("Heat Score 통계")

print(
    nodes["heat_score"]
    .describe()
)

print()

print("최소값:")
print(
    nodes["heat_score"]
    .min()
)

print()

print("최대값:")
print(
    nodes["heat_score"]
    .max()
)

print()

print("heat_grade_norm 통계")

print(
    nodes["heat_grade_norm"]
    .describe()
)

# ====================================
# 8. 저장
# ====================================

nodes.to_file(
    output_path,
    driver="GeoJSON"
)

print()

print("nodes_with_score.geojson 저장 완료")
print(output_path)