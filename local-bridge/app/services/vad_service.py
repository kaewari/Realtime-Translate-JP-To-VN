"""Voice Activity Detection (VAD) service for local-bridge."""
import numpy as np
from app.core.config import config
from app.utils.logger import log_warning

class VADService:
    def __init__(self, energy_threshold: float = None):
        self.threshold = energy_threshold or config.vad_energy_threshold
        
    def is_speech(self, audio_data: np.ndarray, sample_rate: int = 16000) -> bool:
        """Check if audio chunk contains speech using RMS energy calculation."""
        if audio_data is None or len(audio_data) == 0:
            return False
            
        # Ensure float32 array [-1.0, 1.0]
        if audio_data.dtype != np.float32:
            if np.issubdtype(audio_data.dtype, np.integer):
                max_val = float(np.iinfo(audio_data.dtype).max)
                audio_data = audio_data.astype(np.float32) / (max_val if max_val > 0 else 1.0)
            else:
                audio_data = audio_data.astype(np.float32)
                
        rms = np.sqrt(np.mean(np.square(audio_data)))
        return bool(rms >= self.threshold)

    def filter_silence(self, audio_data: np.ndarray, frame_duration_ms: int = 30, sample_rate: int = 16000) -> np.ndarray:
        """Filter out non-speech frames from an audio array."""
        if len(audio_data) == 0:
            return audio_data
            
        frame_size = int(sample_rate * (frame_duration_ms / 1000.0))
        if frame_size <= 0:
            return audio_data
            
        speech_frames = []
        for i in range(0, len(audio_data), frame_size):
            chunk = audio_data[i:i + frame_size]
            if len(chunk) < frame_size / 2:
                continue
            if self.is_speech(chunk, sample_rate):
                speech_frames.append(chunk)
                
        if not speech_frames:
            return np.array([], dtype=np.float32)
            
        return np.concatenate(speech_frames)

vad_service = VADService()
