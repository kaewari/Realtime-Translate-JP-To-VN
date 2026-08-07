"""Pydantic schemas for translation API and WebSocket contracts."""
from typing import Optional, List
from pydantic import BaseModel, Field
import time

class TextTranslationRequest(BaseModel):
    text: str = Field(..., description="Japanese text to translate")
    source_lang: str = Field("ja", description="Source language code")
    target_lang: str = Field("vi", description="Target language code")

class TranslationResponse(BaseModel):
    id: str
    ja_text: str
    vi_text: str
    is_final: bool = True
    confidence: Optional[float] = None
    latency_ms: float = 0.0
    utterance_id: Optional[int] = None  # groups partials + (corrected) finals of one utterance
    timestamp: float = Field(default_factory=time.time)

class ServerStatusResponse(BaseModel):
    status: str = "online"
    asr_engine: str
    mt_engine: str
    sample_rate: int
    uptime_seconds: float
