# Deployment

데이터 없이도 배포 설정은 준비할 수 있습니다.

## Local

```bash
python3 run_server.py
```

Local URL:

```text
http://127.0.0.1:8000
```

## Render

Render에서 repo를 연결하면 `render.yaml` 기준으로 배포할 수 있습니다.

- Build command: `python -m pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/healthcheck`

## Railway

Railway는 `Procfile`의 web command를 사용할 수 있습니다.

```text
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Smoke Test

배포 후 확인:

```bash
curl https://YOUR_BACKEND_URL/healthcheck
```

기대 응답:

```json
{"status":"ok"}
```
