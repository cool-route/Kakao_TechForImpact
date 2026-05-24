from pathlib import Path
import geopandas as gpd

# =========================================
# 경로
# =========================================

BASE_DIR = Path(__file__).resolve().parent.parent

input_path = (
    BASE_DIR
    / "data"
    / "nodes_with_score.geojson"
)

output_path = (
    BASE_DIR
    / "data"
    / "nodes_with_shade.geojson"
)

# =========================================
# 데이터 읽기
# =========================================

gdf = gpd.read_file(input_path)

print("노드 개수:", len(gdf))

# =========================================
# shade 계산 함수
# =========================================

def calculate_shade(row):

    dclsf_cd = str(row.get("dclsf_cd", ""))
    mclsf_cd = str(row.get("mclsf_cd", ""))

    # =====================================
    # 매우 시원
    # 공원 / 녹지 / 산림 계열
    # =====================================

    if dclsf_cd.startswith("GB"):

        return 1.0

    # =====================================
    # 가로수 있는 도로
    # ID2_1
    # =====================================

    if dclsf_cd == "ID2_1":

        return 0.9

    # =====================================
    # 공동주택 / 주거지역
    # =====================================

    if (
        dclsf_cd.startswith("IA")
        or
        mclsf_cd == "IA"
    ):

        return 0.5

    # =====================================
    # 가로수 없는 도로
    # =====================================

    if dclsf_cd == "ID2_2":

        return 0.1

    # =====================================
    # 기타
    # =====================================

    return 0.3

# =========================================
# shade 계산
# =========================================

gdf["shade"] = gdf.apply(
    calculate_shade,
    axis=1
)

# =========================================
# 결과 확인
# =========================================

print("\nshade 분포:")
print(gdf["shade"].value_counts())

print("\nshade 통계:")
print(gdf["shade"].describe())

# =========================================
# 저장
# =========================================

gdf.to_file(
    output_path,
    driver="GeoJSON"
)

print(f"\n저장 완료: {output_path}")
print("\n컬럼 목록:")
print(gdf.columns.tolist())

print("\n첫 행 데이터:")
print(gdf.iloc[0])
print("\ndclsf_cd unique:")
print(gdf["dclsf_cd"].unique()[:20])