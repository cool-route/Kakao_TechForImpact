# Kakao_TechForImpact

## 🎯 프로젝트 목표

경기기후원 데이터를 활용해 수지구 내 **시원한 완성 추천 경로**를 제공하는 웹 서비스

세그먼트 직접 커스텀 ❌ → 기후 데이터 기반 **완성된 추천 경로 13개**를 지도에 표시 ✅

---

## 👥 역할 분담

| 역할 | 담당자 | 한마디 |
| --- | --- | --- |
| 🟦 A — 데이터 엔지니어 | 김주혜 | 기후 데이터를 받아서 "이 길이 얼마나 시원한지" 점수로 만드는 사람 |
| 🟩 B — 백엔드 엔지니어 | 장윤정 | 점수를 받아 "어떤 길이 제일 시원한지" 경로를 계산하고 API로 제공하는 사람 |
| 🟨 C — 프론트 엔지니어 | 조수빈 | 경로를 받아 "사용자가 지도에서 볼 수 있게" 화면을 만드는 사람 |

---

## 🛠 기술 스택

| 레이어 | 기술 | 비고 |
| --- | --- | --- |
| 데이터 수집/처리 | Python, GeoPandas, Shapely, OSMnx | 전부 무료 pip |
| 지도 편집 | QGIS | 무료, ArcGIS 대체 |
| 경로 탐색 | NetworkX (Dijkstra) | 무료 pip |
| 백엔드 | FastAPI | 경량, 무료 |
| DB | SQLite (MVP) | 무료 |
| 지도 시각화 | 카카오맵 JS SDK | 무료 (일 30만 호출) |
| 프론트 | HTML + Vanilla JS | MVP 경량 |
| 배포 — 프론트 | Vercel | 무료 플랜 |
| 배포 — 백엔드 | Render 또는 Railway | 무료 플랜 |
| 협업 | GitHub | 무료 |
| 데이터 공유 | Google Colab | 무료 |

---

## 🆕 최근 업데이트

- 기존 `data/presets.json` 는 Heat Score 계산용 가중치 파일로 유지했습니다.
- 새 프리셋 체계를 별도 파일로 분리했습니다.
  - `data/preset_catalog.json` — STT와 프리셋 수정 UI에서 쓰는 허용 프리셋 마스터 목록
  - `data/route_tags.json` — 사전 생성된 경로별 태그 매핑
  - `data/preset_output_schema.json` — GPT가 프리셋을 추출할 때 사용하는 JSON 스키마
- 프롬프트 정의 문서를 추가했습니다.
  - `docs/PRESET_PROMPTS.md` — 시스템 프롬프트, 사용자 프롬프트, 재시도 프롬프트, OpenAI API messages 예시
- 음성 입력 흐름은 `STT -> GPT 프리셋 추출 -> 사용자 확인/수정 -> 태그 기반 경로 추천` 순서로 정리했습니다.

---

## 📅 Week 1 — 환경 세팅 + 데이터 파악

난이도: ⭐⭐

### 🟦 A — 데이터

- [ ]  경기기후원 데이터 수령 후 파일 형식 확인 (CSV / SHP / API 중 무엇인지)
- [ ]  컬럼 목록 정리 — 온도, UV, 음영, 바람, 좌표 컬럼명 파악 후 팀 공유
- [ ]  결측값 / 이상값 탐색 (EDA) → Google Colab 노트북으로 결과 공유
- [ ]  OSMnx로 수지구 도로 노드/엣지 추출 → `sujiku_roads.geojson` 저장
- [ ]  QGIS에서 기후 데이터 + 도로 레이어 겹쳐보기 (좌표계 범위 맞는지 육안 확인)

### 🟩 B — 백엔드

- [ ]  GitHub 레포 생성 + 팀원 초대 + 브랜치 전략 정의 (`main` / `dev` / 개인 브랜치)
- [ ]  FastAPI 프로젝트 폴더 구조 초기화
- [ ]  SQLite DB 테이블 설계 및 생성 (nodes, routes, shelters)
- [ ]  `/healthcheck` GET API 구현 → C가 연동 테스트할 수 있도록 로컬 공유

### 🟨 C — 프론트

- [ ]  카카오맵 JS SDK 앱 키 발급 ([developers.kakao.com](http://developers.kakao.com))
- [ ]  수지구 중심 좌표로 기본 지도 렌더링 확인 (수지구청: 37.3219, 127.0972)
- [ ]  Figma 무료 플랜으로 와이어프레임 3화면 작성 (메인 / 경로 목록 / 지도 상세)
- [ ]  B의 `/healthcheck` API 연동 테스트

✅ **Week 1 완료 기준**

- 경기기후원 데이터 컬럼 파악 완료 → 팀 공유
- FastAPI 서버 로컬 실행 + `/healthcheck` 응답 확인
- 카카오맵 수지구 지도 브라우저에서 렌더링 확인

---

## 📅 Week 2 — Heat Score 계산 + 경로 탐색 엔진

난이도: ⭐⭐⭐⭐ ← 핵심 난관

### 🟦 A — 데이터

- [ ]  기후 데이터 좌표 → 수지구 도로 노드에 공간 조인 (GeoPandas `sjoin`)
- [ ]  Heat Score 공식 코드 구현: `Score = (w1×온도) + (w2×UV) - (w3×음영) - (w4×바람)`
- [ ]  프리셋 3종 가중치 파일 작성 (`presets.json`) — 기존 Heat Score 가중치 유지
- [ ]  노드별 Score 계산 결과 → `nodes_with_score.geojson` 출력
- [ ]  B에게 GeoJSON 전달 (Week 2 중반까지 필수)

### 🟩 B — 백엔드

- [ ]  A의 `nodes_with_score.geojson` → NetworkX 그래프 변환
- [ ]  Dijkstra에 Heat Score 가중치 적용하여 경로 탐색 구현
- [ ]  `POST /route` API 구현 (요청: mode + start + end → 응답: GeoJSON 경로 + 평균 Score)
- [ ]  3가지 모드 각각 경로 정상 반환 단위 테스트 작성

### 🟨 C — 프론트

- [ ]  `POST /route` API 연동 → 응답 경로 Polyline 지도에 렌더링
- [ ]  Heat Score 기반 경로 색상 구분 (파랑: 시원 / 초록: 보통 / 빨강: 더움)
- [ ]  모드 선택 버튼 3개 UI (노약자 / 반려동물 / 일반)
- [ ]  로딩 스피너 + API 에러 메시지 처리

✅ **Week 2 완료 기준**

- 모드 선택 → `POST /route` 호출 → 지도에 Polyline 렌더링 전체 흐름 동작
- 3가지 프리셋 모두 서로 다른 경로 반환 확인

---

## 📅 Week 3 — 추천 경로 13개 완성 + UI 고도화

난이도: ⭐⭐⭐

### 🟦 A — 데이터

- [ ]  반려동물용: 지면온도 28°C 초과 노드 필터링 로직 완성 → 별도 가중치 적용
- [ ]  노약자용: 수지구 무더위 쉼터 위치 수동 수집 10곳 이상 (주민센터, 도서관, 편의점 등) → `shelters.json` 작성
- [ ]  경로 13개 출발/목적지 좌표쌍 확정 (노약자 5 / 반려동물 5 / 일반 3)
- [ ]  각 경로 GeoJSON 최종 파일 생성 → `data/routes/` 폴더에 저장
- [ ]  C 툴팁용 구간 상세 데이터 제공 (구간별 온도 / 음영비율 / 바람값)

### 🟩 B — 백엔드

- [ ]  노약자 5개 경로 — 쉼터 필수 경유 Waypoint Dijkstra 구현 + DB 저장
- [ ]  반려동물 5개 경로 — 지면온도 낮은 구간 우선 정렬 + DB 저장
- [ ]  일반 3개 경로 — 종합 Heat Score 최솟값 경로 + DB 저장
- [ ]  `GET /routes?mode=노약자` 목록 API 구현 (id, name, heat_score_avg, geojson 반환)
- [ ]  C와 API 응답 스펙 최종 협의 (필드명, 데이터 형식 확정)

### 🟨 C — 프론트

- [ ]  `GET /routes` 연동 → 경로 카드 목록 UI (13개)
- [ ]  경로 카드 클릭 → 해당 경로 지도 하이라이트 (나머지 흐리게)
- [ ]  지도 구간 클릭 → 툴팁 팝업 (체감온도 / 음영비율 / 바람)
- [ ]  쉼터 마커 표시 + 클릭 시 이름 / 운영시간 팝업

✅ **Week 3 완료 기준**

- 13개 경로 전부 지도에서 클릭하여 확인 가능
- 툴팁 팝업 + 쉼터 마커 정상 동작 확인

---

## 📅 Week 4 — 통합 테스트 + 데모 배포

난이도: ⭐⭐⭐

### 🟦 A — 데이터

- [ ]  전체 데이터 파이프라인 문서 작성 (`README_data.md`)
- [ ]  QGIS 또는 Folium으로 Heat Score 히트맵 이미지 생성 (발표용)
- [ ]  경로 13개 선정 근거 정리 (출발/목적지 선택 이유)
- [ ]  데이터 QA 대응 — B/C에서 이상값 발견 시 재보정

### 🟩 B — 백엔드

- [ ]  전체 API 통합 테스트 (`/route`, `/routes`, `/healthcheck`)
- [ ]  Render 또는 Railway 백엔드 무료 배포
- [ ]  FastAPI Swagger 문서 정리 (`/docs` 경로 확인)
- [ ]  응답 속도 측정 → 2초 이상이면 GeoJSON 캐싱 또는 쿼리 최적화 적용

### 🟨 C — 프론트

- [ ]  전체 UI 버그 수정 + 모바일 기본 대응
- [ ]  Vercel 프론트 배포 + 팀 공유 링크 생성
- [ ]  데모 시나리오 3개 스크립트 작성
    - 시나리오 1 — 노약자: 할머니가 병원 가는 쉼터 경유 경로
    - 시나리오 2 — 반려동물: 강아지 산책 지면온도 낮은 경로
    - 시나리오 3 — 일반: 직장인 점심 산책 시원한 경로
- [ ]  A, B, C 최종 통합 테스트 주도 (전체 흐름 1회 시연)

✅ **Week 4 완료 기준**

- 배포된 URL에서 13개 경로 전부 정상 동작
- 데모 시나리오 3개 시연 가능

---

## 🔗 협업 인터페이스

| 전달 | 내용 | 형식 | 시점 |
| --- | --- | --- | --- |
| A → B | 노드별 Heat Score | nodes_with_score.geojson | Week 2 중반 |
| A → B | 쉼터 위치 + 경로 좌표쌍 | shelters.json | Week 3 초반 |
| B → C | 경로 탐색 API 오픈 | POST /route | Week 2 말 |
| B → C | 경로 목록 API 오픈 | GET /routes | Week 3 중반 |
| A → C | 툴팁용 구간 상세 데이터 | JSON | Week 3 중반 |

---

## 📊 전체 타임라인

| 주차 | 핵심 목표 | 난이도 |
| --- | --- | --- |
| Week 1 | 환경 세팅 + 데이터 파악 | ⭐⭐ |
| Week 2 | Heat Score + 경로 탐색 엔진 | ⭐⭐⭐⭐ |
| Week 3 | 13개 추천 경로 + UI 완성 | ⭐⭐⭐ |
| Week 4 | 배포 + 데모 | ⭐⭐⭐ |

⚠️ **리스크:** 경기기후원 데이터 수령이 늦어지면 A가 병목. 데이터 받는 즉시 EDA 결과 팀 공유 최우선.

---

## 🚨 데이터 수령 전 할 수 있는 것 vs 없는 것

### ✅ 지금 당장 가능 (데이터 없어도 됨)

**A**

- OSMnx로 수지구 도로 네트워크 추출
- Heat Score 공식 코드 더미 데이터로 작성 및 테스트
- 프리셋 3종 가중치 파일(`presets.json`) 초안 작성
- QGIS 설치 + 수지구 범위 확인

**B**

- GitHub 레포 + CI 세팅
- FastAPI 프로젝트 구조 초기화
- DB 스키마 설계 + SQLite 세팅
- NetworkX 더미 그래프로 Dijkstra 로직 구현 및 테스트

**C**

- 카카오맵 JS SDK 발급 + 기본 지도 렌더링
- 와이어프레임 3화면 (Figma)
- 모드 선택 UI, 경로 카드 목록 UI 틀 완성
- 더미 좌표로 Polyline 렌더링 테스트
- 툴팁 팝업 UI 틀 완성

### ❌ 데이터 수령 후에만 가능

**A**

- 컬럼 파악 / EDA / 결측값 처리
- 기후 좌표 → 도로 노드 공간 조인
- 실제 Heat Score 계산
- 지면온도 28°C 필터링 (반려동물)
- 쉼터 경유지 구성 (노약자)
- 경로 13개 출발/목적지 확정

**B**

- 실제 GeoJSON → NetworkX 그래프 변환
- 경로 13개 DB 저장
- `/route`, `/routes` 실데이터 연동

**C**

- 더미 → 실 API 교체
- 실제 Heat Score 기반 색상 렌더링
- 실제 쉼터 마커 표시

---

## 📁 파일 구조 (예정)

```
project/
  app/
    main.py
    routers/
      route.py
    models/
      db.py
  data/
    geojson/
      sujiku_roads.geojson
      nodes_with_score.geojson
    routes/
      노약자_01.geojson
      반려동물_01.geojson
      ...
    shelters.json
    presets.json
  frontend/
    index.html
    map.js
    style.css
  README_data.md
  requirements.txt
```

---

## 🔌 API 명세

팀 공유용 고정 JSON 문서는 `docs/api-spec.json`입니다.

- 로컬 기본 주소: `http://127.0.0.1:8000`
- 요청 좌표: `[lat, lng]`
- GeoJSON 좌표: `[lng, lat]`
- mode: `"노약자" | "반려동물" | "일반"`
- 상세 문서: `docs/API_SPEC.md`
- A -> B 데이터 계약: `docs/DATA_CONTRACT.md`

### POST /route

경로 한 개 계산

```json
요청
{
  "mode": "노약자 | 반려동물 | 일반",
  "start": [lat, lng],
  "end": [lat, lng]
}

응답
{
  "path": {
    "type": "FeatureCollection",
    "features": []
  },
  "heat_score_avg": 0.31,
  "distance_m": 1240,
  "shelters": [
    {
      "name": "수지도서관",
      "lat": 37.3232,
      "lng": 127.101,
      "operating_hours": "09:00-18:00"
    }
  ],
  "is_dummy": true
}
```

### GET /routes

추천 경로 목록 조회

```json
요청
GET /routes?mode=노약자

응답
[
  {
    "id": 1,
    "name": "수지구청 → 죽전역",
    "mode": "노약자",
    "heat_score_avg": 0.28,
    "distance_m": 1850,
    "geojson": {
      "type": "FeatureCollection",
      "features": []
    },
    "shelters": [],
    "is_dummy": true
  },
  ...
]
```

### GET /healthcheck

서버 상태 확인

```json
응답: { "status": "ok" }
```

---

## ✅ 데이터 없을 때 선행 작업 우선순위

| 우선순위 | 작업 | 담당 |
| --- | --- | --- |
| 1 | GitHub 레포 세팅 + 브랜치 전략 | B |
| 2 | 카카오맵 SDK 발급 + 기본 지도 렌더링 | C |
| 3 | FastAPI 프로젝트 구조 + DB 스키마 | B |
| 4 | OSMnx 수지구 도로 추출 | A |
| 5 | 와이어프레임 3화면 | C |
| 6 | Heat Score 공식 더미 테스트 | A |
| 7 | Dijkstra 로직 더미 테스트 | B |
| 8 | 더미 Polyline + 툴팁 UI 틀 | C |

---

## 🟩 Backend MVP

데이터 수령 전에도 C가 연동 테스트할 수 있도록 FastAPI 서버와 더미 NetworkX 라우팅 엔진을 먼저 제공합니다.

### 실행

```bash
python3 -m pip install -r requirements.txt
python3 run_server.py
```

기본 주소: `http://127.0.0.1:8000`

### 확인 API

- `GET /healthcheck` -> `{ "status": "ok" }`
- `POST /route` -> 더미 그래프 기반 최적 경로 GeoJSON 반환
- `GET /routes?mode=노약자` -> 더미 추천 경로 목록 반환
- Swagger 문서 -> `http://127.0.0.1:8000/docs`
- 공유용 JSON 명세 -> `docs/api-spec.json`
- A 입력 데이터 계약 -> `docs/DATA_CONTRACT.md`
- 라우팅 정책 -> `docs/ROUTING_POLICY.md`
- 배포 문서 -> `docs/DEPLOYMENT.md`
- 팀 전달 문서 -> `docs/TEAM_HANDOFF.md`
- 프롬프트 정의 -> `docs/PRESET_PROMPTS.md`
- 추천 경로 정의 -> `data/route_specs.json`
- 샘플 데이터 -> `data/sample/nodes_with_score.geojson`, `data/sample/shelters.json`

### 테스트

```bash
python3 -m pytest
```

입력 파일 검증:

```bash
python3 scripts/validate_inputs.py
```

최근 추가한 프리셋 관련 파일:

- `data/preset_catalog.json`
- `data/route_tags.json`
- `data/preset_output_schema.json`

현재 `/route`, `/routes` 응답에는 `"is_dummy": true`가 포함됩니다. A의 `nodes_with_score.geojson`을 `data/geojson/nodes_with_score.geojson`에 넣으면 `/route`는 자동으로 해당 파일을 우선 사용합니다.
