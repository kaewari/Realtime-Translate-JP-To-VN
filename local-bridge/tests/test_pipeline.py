"""Automated unit & integration tests for local-bridge translation pipeline."""
import unittest
import wave
import numpy as np
import base64
import json
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import config
from app.services.vad_service import VADService
from app.services.audio_buffer import AudioBufferManager
from app.services.translation_service import TranslationService
from app.services.asr_service import ASRService

# Golden fixture (gitignored, regenerable): say -v Kyoko -r 160 "こんにちは" -o /tmp/k.aiff
# && ffmpeg -y -i /tmp/k.aiff -ar 16000 -ac 1 -c:a pcm_s16le testdata/audio/konnichiwa-16k.wav
FIXTURE_KONNICHIWA = Path(__file__).resolve().parents[2] / "testdata" / "audio" / "konnichiwa-16k.wav"

class TestLocalBridgePipeline(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.vad = VADService(energy_threshold=0.01)
        self.buffer_mgr = AudioBufferManager(sample_rate=16000)
        self.translator = TranslationService()
        self.asr = ASRService()

    def test_health_endpoint(self):
        """Test GET /health returns status ok."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("service"), "local-bridge")

    def test_status_endpoint(self):
        """Test GET /api/status returns server details."""
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "online")
        self.assertIn("sample_rate", data)

    def test_rest_translate(self):
        """Test POST /api/translate with Japanese text."""
        payload = {"text": "こんにちは", "source_lang": "ja", "target_lang": "vi"}
        response = self.client.post("/api/translate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("ja_text"), "こんにちは")
        self.assertEqual(data.get("vi_text"), "Xin chào")

    def test_vad_service(self):
        """Test VAD energy calculation for silence vs signal."""
        silence = np.zeros(16000, dtype=np.float32)
        signal = np.sin(np.linspace(0, 440 * 2 * np.pi, 16000), dtype=np.float32) * 0.5
        
        self.assertFalse(self.vad.is_speech(silence))
        self.assertTrue(self.vad.is_speech(signal))

    def _feed(self, seconds, amplitude=0.0, chunk_sec=0.1):
        """Feed `seconds` of sine (speech) or zeros (silence) in chunk_sec chunks."""
        for _ in range(int(round(seconds / chunk_sec))):
            n = int(chunk_sec * 16000)
            if amplitude:
                chunk = (np.sin(2 * np.pi * 440 * np.arange(n) / 16000) * amplitude).astype(np.float32)
            else:
                chunk = np.zeros(n, dtype=np.float32)
            self.buffer_mgr.add_float32(chunk)

    def test_audio_buffer(self):
        """Test AudioBufferManager accumulating base64 pcm16."""
        dummy_pcm = (np.sin(np.linspace(0, 440 * 2 * np.pi, 16000)) * 10000).astype(np.int16)
        raw_bytes = dummy_pcm.tobytes()
        b64_str = base64.b64encode(raw_bytes).decode('utf-8')

        self.buffer_mgr.add_base64_pcm16(b64_str)
        window = self.buffer_mgr.pop_utterance(flush=True)
        self.assertIsNotNone(window)
        self.assertGreater(len(window), 0)

    def test_pop_utterance_speech_then_silence(self):
        """Speech 2s + silence 0.7s -> exactly one emit of the 2s speech (trailing silence trimmed)."""
        self._feed(2.0, amplitude=0.5)
        self._feed(0.7)  # silence
        window = self.buffer_mgr.pop_utterance()
        self.assertIsNotNone(window)
        self.assertEqual(len(window), 2 * 16000)  # ~2s, no trailing silence
        self.assertIsNone(self.buffer_mgr.pop_utterance())  # nothing left

    def test_pop_utterance_continuous_below_max(self):
        """Continuous speech < max_utterance_sec -> 0 emits; flush emits it."""
        self._feed(7.0, amplitude=0.5)
        self.assertIsNone(self.buffer_mgr.pop_utterance())
        window = self.buffer_mgr.pop_utterance(flush=True)
        self.assertIsNotNone(window)
        self.assertEqual(len(window), 7 * 16000)

    def test_pop_utterance_max_cap(self):
        """Continuous speech >= max_utterance_sec -> exactly one emit at the cap."""
        self._feed(8.0, amplitude=0.5)
        window = self.buffer_mgr.pop_utterance()
        self.assertIsNotNone(window)
        self.assertEqual(len(window), 8 * 16000)
        self.assertIsNone(self.buffer_mgr.pop_utterance())

    def test_asr_service_mock(self):
        """Unit: ASR returns model text with mocked pipe — no model load, fast."""
        class FakePipe:
            def transcribe(self, audio, **kwargs):
                self.kwargs = kwargs
                return {"text": "こんにちは"}
        fake = FakePipe()
        self.asr.pipe = fake
        self.asr.is_loaded = True
        self.asr.model_path = "mock"
        signal = np.sin(np.linspace(0, 440 * 2 * np.pi, 16000), dtype=np.float32) * 0.5
        res = self.asr.transcribe(signal, 16000)
        self.assertEqual(res, {"text": "こんにちは", "confidence": None})
        # mlx contract: language/task must pass through to the engine
        self.assertEqual(fake.kwargs["language"], config.asr_language)
        self.assertEqual(fake.kwargs["task"], "transcribe")

    @unittest.skipUnless(
        FIXTURE_KONNICHIWA.exists(),
        "missing testdata/audio/konnichiwa-16k.wav (gitignored) — regenerate with 'say -v Kyoko -r 160 こんにちは' + ffmpeg 16k mono"
    )
    def test_asr_service_fixture(self):
        """Integration: real mlx-whisper transcribes golden wav (weights from cache)."""
        asr = ASRService()
        self.assertTrue(asr.load_model())
        with wave.open(str(FIXTURE_KONNICHIWA), "rb") as w:
            self.assertEqual((w.getframerate(), w.getnchannels()), (16000, 1))
            raw = w.readframes(w.getnframes())
        audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        res = asr.transcribe(audio, 16000)
        self.assertIn("こんにちは", res.get("text", ""))

    def test_websocket_translation_flow(self):
        """Test WebSocket /ws/translate text payload handling."""
        with self.client.websocket_connect("/ws/translate") as websocket:
            websocket.send_text(json.dumps({"event": "text", "text": "ありがとう"}))
            data = websocket.receive_json()
            self.assertEqual(data.get("ja_text"), "ありがとう")
            self.assertEqual(data.get("vi_text"), "Cảm ơn")

if __name__ == "__main__":
    unittest.main()
