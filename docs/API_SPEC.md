# API Spec

공유 기준 파일은 `docs/api-spec.json`입니다. 프론트와 백엔드는 이 문서의 필드명을 기준으로 맞춥니다.

## Local Server

```bash
python3 run_server.py
```

Base URL: `http://127.0.0.1:8000`

## Fixed Contract

- `mode`: `"노약자" | "반려동물" | "일반"`
- Request 좌표: `[lat, lng]`
- GeoJSON 좌표: `[lng, lat]`
- `is_dummy: true`: 더미 그래프 응답
- `is_dummy: false`: 실데이터 그래프 응답

## Endpoints

### GET /healthcheck

서버 상태 확인.

Response:

```json
{
  "status": "ok"
}
```

### POST /route

출발지, 도착지, 이동 모드에 맞는 경로 1개를 계산합니다.

Request:

```json
{
  "mode": "일반",
  "start": [37.3219, 127.0972],
  "end": [37.3247, 127.1245]
}
```

Response:

```json
{
  "path": {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "geometry": {
          "type": "LineString",
          "coordinates": [[127.0972, 37.3219], [127.101, 37.3232]]
        },
        "properties": {
          "mode": "일반",
          "heat_score": 23.4,
          "distance_m": 365.8,
          "temperature": 29.5,
          "uv": 0.0,
          "shade_ratio": 0.55,
          "wind": 0.45,
          "ground_temp": 28.4,
          "shelter_name": "수지도서관"
        }
      }
    ]
  },
  "heat_score_avg": 23.4,
  "distance_m": 2494.6,
  "shelters": [
    {
      "name": "수지도서관",
      "lat": 37.3232,
      "lng": 127.101,
      "operating_hours": "09:00-18:00"
    }
  ],
  "is_dummy": false
}
```

### GET /routes

추천 경로 목록을 반환합니다. `mode` query가 없으면 전체 13개를 반환합니다.

Query:

- `mode`: optional, `"노약자" | "반려동물" | "일반"`

Examples:

- `GET /routes`
- `GET /routes?mode=노약자`

Response:

```json
[
  {
    "id": 1,
    "name": "수지구청 -> 죽전역 쉼터 경유",
    "mode": "노약자",
    "heat_score_avg": 23.4,
    "distance_m": 2494.6,
    "geojson": {
      "type": "FeatureCollection",
      "features": []
    },
    "shelters": [],
    "is_dummy": false
  }
]
```

## Frontend Tooltip Fields

프론트 지도 툴팁/카드에서 우선 사용할 필드 제안입니다. C와 최종 문구만 맞추면 됩니다.

| API field | UI label suggestion | Note |
| --- | --- | --- |
| `heat_score` | 더위 점수 | 낮을수록 쾌적 |
| `temperature` | 체감온도 | 섭씨 기준 |
| `uv` | 자외선 | 없으면 `0.0` |
| `shade_ratio` | 그늘 비율 | 0~1 비율 |
| `ground_temp` | 지면온도 | 반려동물 모드 핵심 |
| `wind` | 풍속 | 높을수록 더 시원한 경향 |
| `distance_m` | 거리 | 미터 |
| `shelter_name` | 쉼터 | 없으면 `null` 가능 |

## Related Docs

- 데이터 계약: `docs/DATA_CONTRACT.md`
- 라우팅 정책: `docs/ROUTING_POLICY.md`
- 추천 경로 정의: `data/route_specs.json`
- 추천 경로 DB seed: `scripts/seed_routes.py`
- 성능 측정: `docs/PERFORMANCE.md`

## Frontend Example

```js
const API_BASE_URL = "http://127.0.0.1:8000";

const health = await fetch(`${API_BASE_URL}/healthcheck`).then((res) => res.json());

const route = await fetch(`${API_BASE_URL}/route`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    mode: "일반",
    start: [37.3219, 127.0972],
    end: [37.3247, 127.1245]
  })
}).then((res) => res.json());

const params = new URLSearchParams({ mode: "노약자" });
const routes = await fetch(`${API_BASE_URL}/routes?${params}`).then((res) => res.json());
```
