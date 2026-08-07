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
    endpoint_silence_sec: float = 0.2  # confirm end-of-speech with ~0.2s silence (3 chunks @64ms) to avoid premature finals mid-sentence
    resume_grace_sec: float = 0.4  # speech resuming within this window updates the same utterance
    partial_step_sec: float = 0.25  # min cadence between streaming partial decodes
    max_utterance_sec: float = 8.0  # force emit at this buffer length
    min_speech_sec: float = 0.4  # minimum accumulated speech before any emit
    
    # Model config
    asr_model_name: str = "openai/whisper-small"  # small: 50-63ms/0.5s, ~140-850ms/6.6s decode — best accuracy; tiny is 3x faster but much worse on TTS
    asr_language: str = "ja"
    asr_device: str = "mps"  # cpu or mps for PyTorch on Mac (falls back to cpu if MPS unavailable)
    
    mt_model_name: str = "Helsinki-NLP/opus-mt-ja-vi"
    mt_device: str = "cpu"

config = AppConfig()
