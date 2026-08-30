# manual_test_agent.py
import asyncio

from agent_client import call_preset_agent

async def main():
    text = await call_preset_agent("유모차와 함께 그늘이 많은 길로 1시간 정도 산책할 경로를 찾고 있습니다.")
    print("=== 조립된 전체 텍스트 ===")
    print(text)
    print()
    print("길이:", len(text), "chars")

asyncio.run(main())
