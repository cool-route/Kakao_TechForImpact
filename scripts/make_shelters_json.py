from pathlib import Path

import pandas as pd
import json
import time

from geopy.geocoders import Nominatim

# =========================================
# 경로 설정
# =========================================

BASE_DIR = Path(__file__).resolve().parent.parent

csv_path = (
    BASE_DIR
    / "data"
    / "shelters.csv"
)

output_path = (
    BASE_DIR
    / "data"
    / "shelters.json"
)

# =========================================
# CSV 읽기
# =========================================

df = pd.read_csv(csv_path)

# =========================================
# 지오코더 생성
# =========================================

geolocator = Nominatim(
    user_agent="cool_route_project"
)

results = []

# =========================================
# 주소 → 좌표 변환
# =========================================

for idx, row in df.iterrows():

    name = row["name"]
    address = row["address"]
    shelter_type = row["type"]

    try:

        location = geolocator.geocode(address)

        if location is None:

            print(f"[실패] {name}")
            continue

        result = {

            "name": name,

            "type": shelter_type,

            "address": address,

            "lat": location.latitude,

            "lon": location.longitude

        }

        results.append(result)

        print(f"[완료] {name}")

        # 과도한 요청 방지
        time.sleep(1)

    except Exception as e:

        print(f"[에러] {name}: {e}")

# =========================================
# 결과 확인
# =========================================

print()

print("총 쉼터 개수:")
print(len(results))

# =========================================
# JSON 저장
# =========================================

with open(
    output_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        results,
        f,
        ensure_ascii=False,
        indent=2
    )

print()
print("shelters.json 생성 완료")
print(output_path)