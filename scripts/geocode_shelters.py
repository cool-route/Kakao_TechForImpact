"""shelters.csv (경로당/주민센터) 주소를 카카오 Local API로 geocode하여
shelters_geocoded.json 생성. 이후 shelters.json에 수동 병합 가능.

Usage:
    KAKAO_API_KEY=<REST_API_KEY> python scripts/geocode_shelters.py
"""
from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

import requests

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CSV_PATH = DATA_DIR / "shelters.csv"
OUTPUT_PATH = DATA_DIR / "shelters_geocoded.json"

KAKAO_GEOCODE_URL = "https://dapi.kakao.com/v2/local/search/address.json"


def geocode_address(address: str, api_key: str) -> tuple[float, float] | None:
    headers = {"Authorization": f"KakaoAK {api_key}"}
    resp = requests.get(KAKAO_GEOCODE_URL, headers=headers, params={"query": address}, timeout=5)
    resp.raise_for_status()
    documents = resp.json().get("documents", [])
    if not documents:
        return None
    doc = documents[0]
    return float(doc["y"]), float(doc["x"])  # lat, lng


def main() -> None:
    api_key = os.getenv("KAKAO_API_KEY")
    if not api_key:
        sys.exit("KAKAO_API_KEY 환경변수를 설정하세요. (카카오 개발자 콘솔 REST API 키)")

    results: list[dict] = []
    with CSV_PATH.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row["name"].strip()
            address = row["address"].strip()
            shelter_type = row["type"].strip()

            # address 컬럼이 type과 같거나 비어있으면 유효한 주소가 아님
            if not address or address == shelter_type:
                print(f"  SKIP (주소 없음): {name}")
                continue

            coords = geocode_address(address, api_key)
            if coords is None:
                print(f"  FAIL (geocode 실패): {name} / {address}")
                continue

            lat, lng = coords
            results.append({
                "name": name,
                "lat": lat,
                "lng": lng,
                "address": address,
                "operating_hours": "09:00-18:00",
                "type": shelter_type,
            })
            print(f"  OK: {name} → ({lat:.6f}, {lng:.6f})")

    OUTPUT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{len(results)}개 geocode 완료 → {OUTPUT_PATH}")
    print("결과를 확인 후 data/shelters.json에 병합하세요.")


if __name__ == "__main__":
    main()
