# Data Contract (A → B)

A가 B에게 넘길 파일 형식을 고정합니다.

## 현재 연동 상태

| 파일 | 상태 | 비고 |
|---|---|---|
| `data/nodes_with_score.geojson` | ✅ 연동 완료 | 노드별 Heat Score |
| `data/sujiku_edges.geojson` | ✅ 연동 완료 | 수지구 도로 엣지 |
| `data/shelters.json` | ⏳ 대기 중 | A가 실제 쉼터 10곳 수집 후 전달 |
| `data/route_specs.json` | ⏳ 대기 중 | A가 경로 13개 출발/목적지 확정 후 B가 업데이트 |

---

## nodes_with_score.geojson

GeoJSON `FeatureCollection`. 각 feature는 도로 **노드 하나**를 나타내는 `Point`.

좌표 순서: `[lng, lat]`

필수 properties:

```json
{
  "osmid": 414694370,
  "y": 37.3210302,
  "x": 127.0974709,
  "utci": 27.22,
  "heat": 30.07,
  "shade": 0.60,
  "wind": 2.57,
  "score": 19.53
}
```

필드 설명:

| 필드 | 설명 | 단위 |
|---|---|---|
| `osmid` | OSM 노드 ID (엣지의 u/v와 매칭) | 정수 |
| `utci` | 체감온도 (UTCI 기반) | °C |
| `heat` | 지열 / 지면 더위 지수 | °C |
| `shade` | 천공개폐율 (0=완전 그늘, 1=직사) | 0–1 |
| `wind` | 풍속 | m/s |
| `score` | 종합 Heat Score (낮을수록 시원) | 무단위 |

---

## sujiku_edges.geojson

GeoJSON `FeatureCollection`. 각 feature는 도로 구간 하나를 나타내는 `LineString`.

필수 properties:

```json
{
  "u": 414694370,
  "v": 7857963328,
  "length": 16.36
}
```

| 필드 | 설명 |
|---|---|
| `u` | 출발 노드 osmid |
| `v` | 도착 노드 osmid |
| `length` | 구간 길이 (미터) |

> B는 u/v로 nodes_with_score에서 노드 속성을 조회하고 평균내어 엣지 가중치를 계산합니다.

---

## shelters.json (⏳ 미수령)

무더위쉼터 배열. A가 수집 후 `data/shelters.json`에 저장하면 자동 연동됩니다.

필수 필드:

```json
[
  {
    "name": "수지도서관",
    "lat": 37.3232,
    "lng": 127.101,
    "operating_hours": "09:00-18:00"
  }
]
```

> 현재는 `data/sample/shelters.json` (2개)로 임시 동작 중.

---

## route_specs.json (⏳ 미확정)

13개 추천 경로 출발/목적지. A가 좌표쌍 확정 후 B에게 공유하면 `data/route_specs.json` 업데이트합니다.

```json
[
  {
    "id": 1,
    "mode": "노약자",
    "name": "수지구청 → 죽전역 쉼터 경유",
    "start": [37.3219, 127.0972],
    "end": [37.3247, 127.1245]
  }
]
```

모드별 배분: 노약자 5개 / 반려동물 5개 / 일반 3개

---

## Backend Loader

```python
from app.services.geojson_loader import load_graph_from_nodes_and_edges, load_shelters

graph = load_graph_from_nodes_and_edges(
    "data/nodes_with_score.geojson",
    "data/sujiku_edges.geojson",
    shelters_path="data/shelters.json",
)
```

그래프는 서버 시작 후 첫 요청 시 로드되고 메모리에 캐싱됩니다.

## Validation

```bash
python3 scripts/validate_inputs.py \
  --nodes data/nodes_with_score.geojson \
  --shelters data/shelters.json \
  --routes data/route_specs.json
```
