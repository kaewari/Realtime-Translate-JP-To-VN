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

vad_service = VADService()
