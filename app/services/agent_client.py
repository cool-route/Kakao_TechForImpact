import json
import os
from pathlib import Path

from dotenv import load_dotenv
try:
    import httpx
except ImportError:
    httpx = None

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

AGENT_URL = "https://climatepod-agent-snowy.vercel.app/chat"
AGENT_API_KEY = os.environ.get("CLIMATEPOD_AGENT_KEY")  # 없으면 인증 없이 호출


async def call_preset_agent(message: str, conversation_id: str | None = None) -> str:
    if httpx is None:
        raise RuntimeError("httpx 라이브러리가 설치되어 있지 않습니다.")
    headers = {"Content-Type": "application/json"}
    if AGENT_API_KEY:
        headers["x-api-key"] = AGENT_API_KEY  # Bearer 접두사 없이 값 그대로

    payload = {"message": message}
    if conversation_id:
        payload["conversation_id"] = conversation_id

    full_text = ""
    async with httpx.AsyncClient(timeout=30) as client:
        async with client.stream("POST", AGENT_URL, json=payload, headers=headers) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line[len("data: "):]
                if data == "[DONE]":
                    break
                chunk = json.loads(data)
                full_text += chunk.get("content", "")
    return full_text
