"""Automated unit & integration tests for local-bridge translation pipeline."""
import unittest
import numpy as np
import base64
import json
from fastapi.testclient import TestClient

from app.main import app
from app.services.vad_service import VADService
from app.services.audio_buffer import AudioBufferManager
from app.services.translation_service import TranslationService
from app.services.asr_service import ASRService

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

    def test_audio_buffer(self):
        """Test AudioBufferManager accumulating base64 pcm16."""
        dummy_pcm = (np.sin(np.linspace(0, 440 * 2 * np.pi, 16000)) * 10000).astype(np.int16)
        raw_bytes = dummy_pcm.tobytes()
        b64_str = base64.b64encode(raw_bytes).decode('utf-8')

        self.buffer_mgr.add_base64_pcm16(b64_str)
        window = self.buffer_mgr.get_window(max_seconds=2.0, min_seconds=0.5)
        self.assertIsNotNone(window)
        self.assertGreater(len(window), 0)

    def test_asr_service(self):
        """Test ASR service returns non-empty result dict."""
        signal = np.sin(np.linspace(0, 440 * 2 * np.pi, 16000), dtype=np.float32) * 0.5
        res = self.asr.transcribe(signal, 16000)
        self.assertIn("text", res)
        self.assertIn("confidence", res)

    def test_websocket_translation_flow(self):
        """Test WebSocket /ws/translate text payload handling."""
        with self.client.websocket_connect("/ws/translate") as websocket:
            websocket.send_text(json.dumps({"event": "text", "text": "ありがとう"}))
            data = websocket.receive_json()
            self.assertEqual(data.get("ja_text"), "ありがとう")
            self.assertEqual(data.get("vi_text"), "Cảm ơn")

if __name__ == "__main__":
    unittest.main()
