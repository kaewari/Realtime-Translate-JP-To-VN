"""Automatic Speech Recognition (ASR) service for Japanese audio."""
import numpy as np
from typing import Dict, Any, Optional
from app.core.config import config
from app.utils.logger import log_error, log_warning

# Whisper often invents these on silence / trailing noise (classic YouTube outro).
_WHISPER_JUNK = frozenset({
    "ご視聴ありがとうございました",
    "ご視聴ありがとう",
    "thanksforwatching",
    "チャンネル登録",
    "高評価",
    "共有",
    "コメント",
    "登録",
    "いいね",
    "通知",
    "概要欄",
})


def _filter_whisper_junk(text: str) -> str:
    compact = "".join(text.split()).strip("。．.!！?？").lower()
    return "" if compact in _WHISPER_JUNK else text.strip()


class ASRService:
    def __init__(self):
        self.pipe = None
        self.is_loaded = False
        self.load_failed = False
        self.engine_name = "Whisper (Pending)"

    def load_model(self):
        """Lazy load ASR model (transformers pipeline or fallback)."""
        if self.is_loaded:
            return True
        try:
            import mlx_whisper

            model_name = config.asr_model_name
            # If using standard openai model, map to mlx-community for speed
            if model_name == "openai/whisper-small":
                model_name = "mlx-community/whisper-small-mlx"

            self.pipe = mlx_whisper
            self.model_path = model_name
            
            # Warmup to cache weights
            self.pipe.transcribe(np.zeros(16000, dtype=np.float32), path_or_hf_repo=self.model_path)
            
            self.is_loaded = True
            self.engine_name = f"mlx-{model_name.split('/')[-1]}"
            return True
        except Exception as e:
            log_warning(f"Could not initialize ASR model '{config.asr_model_name}': {e}. Using fallback/mock ASR.")
            self.is_loaded = False
            self.load_failed = True  # never retry — retrying per window spams errors.log
            self.engine_name = "fallback-asr (load failed)"
            return False

    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Dict[str, Any]:
        """Transcribe PCM float32 audio numpy array into Japanese text."""
        if audio_data is None or len(audio_data) == 0:
            return {"text": "", "confidence": 0.0}

        # Lazy load if needed — skip retry once a load attempt has failed
        if not self.is_loaded and not self.load_failed:
            self.load_model()

        if self.is_loaded and self.pipe:
            try:
                # Ensure float32 array
                if audio_data.dtype != np.float32:
                    audio_data = audio_data.astype(np.float32)
                res = self.pipe.transcribe(
                    audio_data,
                    path_or_hf_repo=self.model_path,
                    language=config.asr_language,
                    task="transcribe",
                    temperature=0.0,
                    no_speech_threshold=0.6,
                    condition_on_previous_text=False
                )
                text = _filter_whisper_junk(res.get("text", ""))
                return {"text": text, "confidence": None}
            except Exception as e:
                log_error(f"ASR transcribe error: {e}")

        # Fallback ASR for non-empty audio signals (detect audio energy pattern for test/dev)
        rms = float(np.sqrt(np.mean(np.square(audio_data))))
        if rms < config.vad_energy_threshold:
            return {"text": "", "confidence": 0.0}

        # Safe placeholder phrase for active audio chunks in local dev when model not downloaded yet
        return {"text": "こんにちは、リアルタイム翻訳テストです。", "confidence": None}

asr_service = ASRService()
