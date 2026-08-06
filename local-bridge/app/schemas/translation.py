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
    confidence: float = 1.0
    latency_ms: float = 0.0
    timestamp: float = Field(default_factory=time.time)

class AudioChunkMessage(BaseModel):
    event: str = "audio_chunk"  # "audio_chunk", "ping", "stop"
    audio_base64: Optional[str] = None
    sample_rate: int = 16000
    is_final: bool = False

class ServerStatusResponse(BaseModel):
    status: str = "online"
    asr_engine: str
    mt_engine: str
    sample_rate: int
    uptime_seconds: float
