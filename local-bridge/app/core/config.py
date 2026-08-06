"""Application configuration for local-bridge."""
import os
from pydantic import BaseModel

class AppConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8765
    
    # Audio config
    sample_rate: int = 16000
    channels: int = 1
    sample_width: int = 2  # 16-bit PCM

    # VAD config
    vad_energy_threshold: float = 0.015  # RMS threshold for energy VAD
    vad_enabled: bool = True

    # Utterance endpointing (silence-based)
    endpoint_silence_sec: float = 0.6  # trailing silence before emitting an utterance
    max_utterance_sec: float = 8.0  # force emit at this buffer length
    min_speech_sec: float = 0.4  # minimum accumulated speech before any emit
    
    # Model config
    asr_model_name: str = "openai/whisper-small"
    asr_language: str = "ja"
    asr_device: str = "mps"  # cpu or mps for PyTorch on Mac (falls back to cpu if MPS unavailable)
    
    mt_model_name: str = "Helsinki-NLP/opus-mt-ja-vi"
    mt_device: str = "cpu"

config = AppConfig()
