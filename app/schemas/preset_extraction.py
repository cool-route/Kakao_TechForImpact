from pydantic import BaseModel, Field


class PresetExtractionRequest(BaseModel):
    """프론트 SearchFlow.tsx의 recognizedText를 받는 요청 모양"""
    text: str = Field(..., description="사용자가 확인/수정한 STT 텍스트 (recognizedText)")


class PresetExtractionEcho(BaseModel):
    """1단계(수신 확인) 전용 임시 응답 — GPT 연동 전까지만 사용"""
    received_text: str