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
    window_duration_sec: float = 3.0  # sliding window for ASR

    # VAD config
    vad_energy_threshold: float = 0.015  # RMS threshold for energy VAD
    vad_enabled: bool = True
    
    # Model config
    asr_model_name: str = "openai/whisper-small"
    asr_language: str = "ja"
    asr_device: str = "mps"  # cpu or mps for PyTorch on Mac (falls back to cpu if MPS unavailable)
    
    mt_model_name: str = "Helsinki-NLP/opus-mt-ja-vi"
    mt_device: str = "cpu"

config = AppConfig()
