# Walkthrough — Realtime Translate JP To VN

> **Trạng thái: MVP Verified** (2026-08-06). Đã triển khai đầy đủ backend `local-bridge` (FastAPI + WebSocket + VAD + ASR + MarianMT) và Web Studio UI.

## Cấu trúc thư mục

```
Realtime Translate JP To VN/
├── local-bridge/           # Backend Python (FastAPI + WebSocket, port 8765)
│   ├── app/
│   │   ├── api/            # REST & WebSocket endpoints (/ws/translate, /health, /api/translate)
│   │   ├── core/           # Config (AppConfig, sample rate 16kHz, VAD threshold)
│   │   ├── schemas/        # Pydantic data schemas (TextTranslationRequest, TranslationResponse)
│   │   ├── services/       # VAD, ASR, Translation (MarianMT + Fallback), AudioBuffer
│   │   ├── utils/          # Logger utility (writes to local-bridge/errors.log per AGENTS §6)
│   │   └── main.py         # App entrypoint & static Web UI mounting
│   ├── tests/              # Automated unit/integration test suite (7 tests)
│   ├── requirements.txt    # Package dependencies
│   └── errors.log          # Runtime & error log file
├── web/
│   └── index.html          # Modern Web Studio UI (Dark Mode, Web Audio API, WebSocket)
├── plan/                   # Active implementation plans
├── wiki/                   # LLM wiki
└── walkthrough.md          # Realtime pipeline walkthrough & test documentation
```

## Kiến trúc audio pipeline

```
Microphone (Web Audio API) ──▶ Base64 PCM16 ──▶ WebSocket (/ws/translate)
                                                        │
                                                        ▼
                                               AudioBufferManager
                                                        │
                                                        ▼
                                                RMS Energy VAD
                                                        │
                                                        ▼
                                               Japanese ASR Engine
                                                        │
                                                        ▼
                                            Translation Engine (MarianMT)
                                                        │
                                                        ▼
                                         WebSocket Response JSON {ja_text, vi_text, latency_ms}
```

- **Capture**: Web Audio API (ScriptProcessor — AudioWorklet chưa dùng) – PCM 16kHz mono.
- **VAD**: RMS Energy Voice Activity Detector (`vad_service.py`) loại bỏ khoảng yên lặng.
- **Buffer**: `AudioBufferManager` quản lý sliding window 1.5s - 3.0s.
- **ASR**: `ASRService` nhận diện giọng nói tiếng Nhật (`openai/whisper-small` / fallback ASR engine).
- **Translation**: `TranslationService` dịch Nhật→Việt bằng MarianMT (`Helsinki-NLP/opus-mt-ja-vi`) kết hợp Từ điển hạt giống (Seed Dictionary Fallback).
- **Delivery**: WebSocket gửi kết quả `TranslationResponse` JSON trực tiếp lên UI.

## Kết quả kiểm thử (Automated Tests Verification)

Toàn bộ 7 bài test đã chạy thành công trong 5.038s (`python3 -m unittest discover -s tests`):

1. `test_health_endpoint` (REST GET `/health` -> status 200 OK)
2. `test_status_endpoint` (REST GET `/api/status` -> server status online)
3. `test_rest_translate` (REST POST `/api/translate` -> dịch chính xác "こんにちは" thành "Xin chào")
4. `test_vad_service` (VAD nhận diện chính xác tiếng nói vs khoảng im lặng)
5. `test_audio_buffer` (AudioBuffer tích tụ và giải phóng PCM16 base64 window đúng kích thước)
6. `test_asr_service` (ASR trả về text & confidence score)
7. `test_websocket_translation_flow` (WebSocket giao tiếp JSON hai chiều realtime thành công)

## Tính năng mới (D-UX Sprint 1)

- **UX1 (Mic Selector):** Tự động `enumerateDevices` và hiển thị UI để người dùng chọn thiết bị đầu vào (Microphone) tuỳ ý thay vì luôn dùng mic mặc định.
- **UX2 (Export):** Thêm nút **Export** để tải toàn bộ transcript hiện tại (Nhật + Việt) dưới dạng file Markdown (`.md`) kèm timestamp.
- **UX3 (Sửa Text JA):** Hỗ trợ click đúp (double-click) vào câu tiếng Nhật để chỉnh sửa trực tiếp. Khi nhấn Enter, hệ thống gọi API `/api/translate` dịch lại và cập nhật thẻ tiếng Việt tương ứng.
- **UX4 (Phím tắt Space):** Hỗ trợ dùng phím Space (dấu cách) để bật/tắt nhanh microphone. Tự động bỏ qua khi người dùng đang gõ phím vào ô input/textarea.
- **UX5 (Xử lý Offline):** Cải thiện trải nghiệm khi mất kết nối WebSocket. Tự động dừng thu âm, khoá nút thu âm và hiển thị trạng thái đang thử kết nối lại một cách rõ ràng.

## Tính năng mới (D-UX Sprint 1)

- **UX1 (Mic Selector):** Tự động `enumerateDevices` và hiển thị UI để người dùng chọn thiết bị đầu vào (Microphone) tuỳ ý thay vì luôn dùng mic mặc định.
- **UX2 (Export):** Thêm nút **Export** để tải toàn bộ transcript hiện tại (Nhật + Việt) dưới dạng file Markdown (`.md`) kèm timestamp.
- **UX3 (Sửa Text JA):** Hỗ trợ click đúp (double-click) vào câu tiếng Nhật để chỉnh sửa trực tiếp. Khi nhấn Enter, hệ thống gọi API `/api/translate` dịch lại và cập nhật thẻ tiếng Việt tương ứng.
- **UX4 (Phím tắt Space):** Hỗ trợ dùng phím Space (dấu cách) để bật/tắt nhanh microphone. Tự động bỏ qua khi người dùng đang gõ phím vào ô input/textarea.
- **UX5 (Xử lý Offline):** Cải thiện trải nghiệm khi mất kết nối WebSocket. Tự động dừng thu âm, khoá nút thu âm và hiển thị trạng thái đang thử kết nối lại một cách rõ ràng.

## Hướng dẫn chạy thử

1. Cài dependencies (⚠️ `scipy==1.14.1` bắt buộc — wheel scipy≥1.15 fail dyld trên macOS 27 + Python 3.10 → ASR fallback mock âm thầm):
   ```bash
   cd local-bridge && pip install -r requirements.txt
   ```
2. Chạy Backend Server:
   ```bash
   cd local-bridge && uvicorn app.main:app --port 8765
   ```
   Lần dùng đầu: models (whisper-small, opus-mt-ja-vi) tự download vào HF cache và lazy-load (~10-30s cho gọi đầu).
3. Mở giao diện Web Studio:
   - Truy cập `http://localhost:8765/` hoặc mở file `web/index.html`.
4. Bấm **"Bắt đầu thu âm"** để nói trực tiếp hoặc nhập câu tiếng Nhật vào ô text để test độ trễ. Khi bấm **"Dừng thu âm"**, câu cuối được finalize (`is_final=true`, UI thay card cuối thay vì thêm trùng).
5. Để test các tính năng UX mới:
   - Thay đổi Micro từ dropdown kế bên nút thu âm (UX1).
   - Nhấn phím Space để bật/tắt thu âm (UX4).
   - Dịch thử vài câu, nhấn nút **Export** để tải file transcript (UX2).
   - Nhấp đúp vào thẻ kết quả tiếng Nhật, sửa văn bản và nhấn Enter để dịch lại (UX3).
   - Đóng tiến trình server terminal để thử giao diện báo mất kết nối và dừng thu âm (UX5).
5. Để test các tính năng UX mới:
   - Thay đổi Micro từ dropdown kế bên nút thu âm (UX1).
   - Nhấn phím Space để bật/tắt thu âm (UX4).
   - Dịch thử vài câu, nhấn nút **Export** để tải file transcript (UX2).
   - Nhấp đúp vào thẻ kết quả tiếng Nhật, sửa văn bản và nhấn Enter để dịch lại (UX3).
   - Đóng tiến trình server terminal để thử giao diện báo mất kết nối và dừng thu âm (UX5).
