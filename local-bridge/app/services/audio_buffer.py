"""Real-time streaming Audio Buffer manager."""
import base64
import numpy as np
from typing import Optional
from app.core.config import config
from app.services.vad_service import vad_service

class AudioBufferManager:
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.buffer = np.array([], dtype=np.float32)
        self.total_speech_sec = 0.0      # speech accumulated since last emit
        self.trailing_silence_sec = 0.0  # continuous silence since last speech chunk
        self.last_chunk_dur = 0.0        # duration (s) of the most recent added chunk
        self.utterance_generation = 0    # bumped when a confirmed pause starts a new utterance

    def add_base64_pcm16(self, b64_str: str, source_sample_rate: int = None) -> bool:
        """Add base64-encoded 16-bit PCM audio; returns True if chunk classified as speech."""
        try:
            raw_bytes = base64.b64decode(b64_str)
            pcm16 = np.frombuffer(raw_bytes, dtype=np.int16)
            float32_audio = pcm16.astype(np.float32) / 32768.0
            if source_sample_rate and source_sample_rate != self.sample_rate:
                float32_audio = self._resample(float32_audio, source_sample_rate, self.sample_rate)
            return self.add_float32(float32_audio)
        except Exception as e:
            from app.utils.logger import log_error
            log_error(f"Failed to decode base64 pcm16: {e}")
            return False

    @staticmethod
    def _resample(audio_data: np.ndarray, src_rate: int, dst_rate: int) -> np.ndarray:
        """Linear-interp resample to dst_rate.
        # ponytail: naive linear resample, fine for speech VAD/ASR at 16k; swap for soxr if quality suffers."""
        if src_rate == dst_rate or len(audio_data) == 0:
            return audio_data
        n_out = int(round(len(audio_data) * dst_rate / src_rate))
        if n_out == 0:
            return np.array([], dtype=np.float32)
        x_in = np.linspace(0.0, 1.0, len(audio_data), endpoint=False)
        x_out = np.linspace(0.0, 1.0, n_out, endpoint=False)
        return np.interp(x_out, x_in, audio_data).astype(np.float32)

    def add_float32(self, audio_data: np.ndarray) -> bool:
        """Add float32 audio samples; returns True if chunk classified as speech.

        A speech chunk arriving after a pause >= resume_grace_sec is a NEW utterance:
        the previous (already finalized) buffer is dropped so the window starts fresh.
        """
        if audio_data is None or len(audio_data) == 0:
            return False
        self.last_chunk_dur = len(audio_data) / self.sample_rate
        # VAD on tail ~200ms: a chunk mixing speech->silence is judged by its end
        # (ponytail: chunk-level heuristic, fine for ~32-64ms realtime chunks)
        tail = audio_data[-min(len(audio_data), int(self.sample_rate * 0.2)):]
        is_speech = (not config.vad_enabled) or vad_service.is_speech(tail, self.sample_rate)
        if is_speech and self.total_speech_sec > 0 and self.trailing_silence_sec >= config.resume_grace_sec:
            self._reset()
            self.utterance_generation += 1
        if is_speech:
            self.total_speech_sec += self.last_chunk_dur
            self.trailing_silence_sec = 0.0
        else:
            self.trailing_silence_sec += self.last_chunk_dur
        self.buffer = np.concatenate([self.buffer, audio_data])
        return is_speech

    def partial_window(self) -> np.ndarray:
        """Current full window for streaming decode (no reset)."""
        return self.buffer

    def should_emit_final(self) -> bool:
        """Optimistic final: enough speech and the first silence chunk(s) have arrived."""
        return (self.total_speech_sec >= config.min_speech_sec
                and self.trailing_silence_sec >= config.endpoint_silence_sec)

    def should_cap(self) -> bool:
        return len(self.buffer) / self.sample_rate >= config.max_utterance_sec

    def pop_utterance(self, flush: bool = False) -> Optional[np.ndarray]:
        """Legacy path: emit the whole utterance and reset. Flush always emits."""
        if flush:
            window = self.buffer
            self._reset()
            return window if len(window) > 0 else None
        if self.should_emit_final():
            keep = max(0, len(self.buffer) - int(round(self.trailing_silence_sec * self.sample_rate)))
            window = self.buffer[:keep]
            self._reset()
            return window if len(window) > 0 else None
        if self.should_cap():
            if self.total_speech_sec >= config.min_speech_sec:
                window = self.buffer
                self._reset()
                return window
            self._reset()
        return None

    def reset(self) -> None:
        """Clear buffer and endpointing state (public)."""
        self._reset()

    def _reset(self) -> None:
        """Clear buffer and endpointing state."""
        self.buffer = np.array([], dtype=np.float32)
        self.total_speech_sec = 0.0
        self.trailing_silence_sec = 0.0
        self.last_chunk_dur = 0.0
