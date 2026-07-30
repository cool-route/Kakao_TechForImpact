# Team Handoff

B 백엔드가 A/C에게 공유할 문서와 실행 기준입니다.

## A 데이터 담당 확인

필수 확인 문서:

- `docs/DATA_CONTRACT.md`
- `data/sample/nodes_with_score.geojson`
- `data/sample/shelters.json`

A가 전달할 실제 파일 위치:

- `data/geojson/nodes_with_score.geojson`
- `data/shelters.json`

검증 명령:

```bash
python3 scripts/validate_inputs.py \
  --nodes data/geojson/nodes_with_score.geojson \
  --shelters data/shelters.json \
  --routes data/route_specs.json
```

## C 프론트 담당 확인

필수 확인 문서:

- `docs/api-spec.json`
- `docs/API_SPEC.md`

로컬 서버:

```bash
python3 run_server.py
```

```text
http://127.0.0.1:8000
```

연동 API:

- `GET /healthcheck`
- `POST /route`
- `GET /routes`
- `GET /routes?mode=노약자`

주의:

- 요청 좌표는 `[lat, lng]`
- GeoJSON 좌표는 `[lng, lat]`
- `is_dummy: true`면 실데이터 전 더미 응답

## B가 관리하는 파일

- API 계약: `docs/api-spec.json`
- 라우팅 정책: `docs/ROUTING_POLICY.md`
- 추천 경로 13개 정의: `data/route_specs.json`
- 실데이터 로더: `app/services/geojson_loader.py`
- 라우팅 엔진: `app/services/route_service.py`

## STT / preset flow

- 프리셋 카탈로그: `data/preset_catalog.json`
- GPT 출력 스키마: `data/preset_output_schema.json`
- 경로 태그 매핑: `data/route_tags.json`
- 프롬프트 정의: `docs/PRESET_PROMPTS.md`
