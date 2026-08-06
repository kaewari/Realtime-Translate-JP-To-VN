"""Real-time streaming Audio Buffer manager."""
import base64
import numpy as np
from typing import Optional, Tuple, List
from app.core.config import config
from app.services.vad_service import vad_service

class AudioBufferManager:
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.buffer = np.array([], dtype=np.float32)
        self.silence_count = 0

    def add_base64_pcm16(self, b64_str: str) -> None:
        """Add base64-encoded 16-bit PCM audio data to buffer."""
        try:
            raw_bytes = base64.b64decode(b64_str)
            pcm16 = np.frombuffer(raw_bytes, dtype=np.int16)
            float32_audio = pcm16.astype(np.float32) / 32768.0
            self.add_float32(float32_audio)
        except Exception as e:
            from app.utils.logger import log_error
            log_error(f"Failed to decode base64 pcm16: {e}")

    def add_float32(self, audio_data: np.ndarray) -> None:
        """Add float32 audio samples to buffer."""
        if audio_data is None or len(audio_data) == 0:
            return
        self.buffer = np.concatenate([self.buffer, audio_data])

    def get_window(self, max_seconds: float = 3.0, min_seconds: float = 0.5) -> Optional[np.ndarray]:
        """Extract a processable speech window if enough audio accumulated."""
        min_samples = int(self.sample_rate * min_seconds)
        max_samples = int(self.sample_rate * max_seconds)

        if len(self.buffer) < min_samples:
            return None

        # Check if current buffer contains speech via VAD
        if config.vad_enabled:
            is_speech = vad_service.is_speech(self.buffer, self.sample_rate)
            if not is_speech:
                # Flush silence if buffer exceeds max_seconds
                if len(self.buffer) > max_samples:
                    self.buffer = np.array([], dtype=np.float32)
                return None

        # Slice up to max_samples
        samples_to_take = min(len(self.buffer), max_samples)
        window = self.buffer[:samples_to_take]
        
        # Advance buffer by samples_to_take or step
        step = int(self.sample_rate * 1.5)  # 1.5s step for sliding window
        if len(self.buffer) > max_samples:
            self.buffer = self.buffer[step:]
        else:
            self.buffer = np.array([], dtype=np.float32)
            
        return window

    def flush(self) -> np.ndarray:
        """Flush remaining buffer."""
        remaining = self.buffer
        self.buffer = np.array([], dtype=np.float32)
        return remaining

    def clear(self) -> None:
        """Clear buffer state."""
        self.buffer = np.array([], dtype=np.float32)
        self.silence_count = 0
