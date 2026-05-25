import pandas as pd
from pathlib import Path

# 프로젝트 루트 기준 경로
BASE_DIR = Path(__file__).resolve().parent.parent

# 엑셀 파일 경로
file_path = (
    BASE_DIR
    / "data"
    / "vulnerable group data"
    / "용인시_읍면동_취약인구.xlsx"
)

# 엑셀 읽기
df = pd.read_excel(file_path)

# 수지구만 필터링
df_suji = df[df["GU_NM"] == "수지구"]

# 전체 인구
total_pop = df_suji["POP_HJD"].sum()

# 취약계층별 합계
child_total = df_suji["N_CHLD_HJD"].sum()
old_total = df_suji["N_OLD_HJD"].sum()
disb_total = df_suji["N_DISB_HJD"].sum()
heati_total = df_suji["N_HEATI_HJD"].sum()
chroi_total = df_suji["N_CHROI_HJD"].sum()

# 비율 계산
result = {
    "어린이 비율": child_total / total_pop * 100,
    "노인 비율": old_total / total_pop * 100,
    "장애인 비율": disb_total / total_pop * 100,
    "온열질환 취약 비율": heati_total / total_pop * 100,
    "만성질환자 비율": chroi_total / total_pop * 100,
}

for k, v in result.items():
    print(f"{k}: {v:.2f}%")