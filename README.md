# Realtime Translate JP To VN

Dịch giọng nói **tiếng Nhật → tiếng Việt** theo thời gian thực (near real-time), local-first, tối ưu cho Apple Silicon.

> **Trạng thái: MVP Ready + verified** (2026-08-06) — Backend local-bridge (FastAPI + WebSocket + VAD + ASR + MarianMT) & Web Studio UI đã hoàn thiện; review claims đã verify trên máy thật (ASR whisper-small, MT MarianMT, E2E WS với audio thật).

## Giới thiệu

Thu âm từ micro, nhận diện giọng nói tiếng Nhật bằng ASR cục bộ, dịch sang tiếng Việt bằng model dịch máy cục bộ, và hiển thị kết quả qua UI theo thời gian thực. Ưu tiên độ trễ thấp ("near real-time"), toàn bộ xử lý chạy trên máy (local-first, không gọi MT API).

## Ràng buộc máy (đã kiểm tra 2026-08-05)

| Hạng mục | Giá trị |
|---|---|
| Máy | MacBook Pro – Apple M5 Pro (15 core CPU) |
| RAM | 24 GB unified |
| GPU | Apple GPU M5 Pro (Metal 4) — **không CUDA** |
| OS | macOS 27.0 |
| Python | 3.10.6 (dùng venv riêng) |
| ffmpeg | 8.1.2 tại `/opt/homebrew/bin/ffmpeg` |

→ Không dùng CUDA; tăng tốc bằng **Metal / MLX / MPS** (whisper.cpp Metal hoặc mlx-whisper cho ASR; PyTorch MPS cho translation).

## Stack

- Backend: **Python + FastAPI + WebSocket** (`local-bridge/`, port 8765)
- VAD: **RMS Energy VAD** (`app/services/vad_service.py`)
- ASR: **Whisper / Fallback ASR** (`app/services/asr_service.py`) — `language: ja`
- Translation: **Helsinki-NLP/opus-mt-ja-vi** (MarianMT + Offline Dict Fallback)
- Audio Buffer: **Streaming PCM16 Base64 Buffer Manager** (`app/services/audio_buffer.py`)
- UI: Web Studio (`web/index.html` - HTML5, CSS Glassmorphism, Web Audio API)

## Cấu trúc thư mục

```
extension/          # (TBD) Chrome extension
local-bridge/       # Backend Python: app/{api,core,schemas,services,utils}/main.py
macos-bridge-app/   # (TBD) macOS bridge app
ipad-app/           # (TBD) iPad app
iphone-app/         # (TBD) iPhone app
data/               # config / dict / subtitles (runtime, gitignored phần lớn)
scripts/            # (TBD) scripts tiện ích
testdata/           # fixture test / golden audio
tools/ime-switch/   # (TBD) IME switch cho input tiếng Nhật
web/saved-items/    # (TBD) web app lưu bản dịch
skills/             # 5 skill (ponytail, codegraph, realtime-translate, local-bridge, realtime-regression)
wiki/               # LLM wiki (Karpathy pattern)
plan/ review/       # plan/review file (bất biến, wiki là tổng hợp sống)
```

## Quickstart

1. `cd local-bridge && python3.10 -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt` — ⚠️ bắt buộc `scipy==1.14.1` (đã pin): wheel scipy≥1.15 fail dyld trên macOS 27 với Python 3.10 → ASR âm thầm fallback mock; và `sentencepiece` (MarianTokenizer) — thiếu → MT FallbackDict, UI hiện `[Dịch: …]`
3. `uvicorn app.main:app --port 8765`
4. Mở <http://localhost:8765/> — models (whisper-small, opus-mt-ja-vi) tự download vào HF cache `~/.cache/huggingface/hub/` và **preload background ngay khi server start** (gọi đầu không còn stall ~1.7s)
5. (Tùy chọn) `curl localhost:8765/api/status` — xem engine ASR/MT đã load chưa

## Streaming translate

Dịch **liên tục khi đang nói** như web dịch hiện đại: partial xuất hiện ~0.4s sau khi bắt đầu và tự sửa khi có thêm audio (ASR/MT chạy background, loop WS không block); final re-decode window cuối nên không bao giờ cắt cụt đuôi câu. Số đo thật (10 câu dài, whisper-small): final p50 ~324ms, accuracy 7/10 exact — chi tiết trong [walkthrough](walkthrough.md).

## Lộ trình

| Phase | Nội dung | Trạng thái |
|---|---|---|
| 1 | PoC nhanh — thu micro → ASR → dịch → in text | ✅ done |
| 2 | Near real-time — VAD, chunking, sentence buffer | ✅ done |
| 3 | UI/UX — JA+VI, export, mic, Space, sửa JA; PiP, restore F5, TTS VI, manifest | ✅ done (D-UX S1+S2) |
| 4 | Tối ưu hiệu năng — Metal/quantization (whisper.cpp/MLX) | ✅ done 2026-08-06 (mlx-whisper, ~63ms/window) |

Chi tiết: `plan/plan-2026-08-05-realtime-translate-jp-to-vn.md`.

## Docs khác

- `walkthrough.md` — kiến trúc audio pipeline + hướng dẫn chạy (đầy đủ)
- `AGENTS.md` — quy ước bắt buộc cho mọi agent (ponytail, plan/review, wiki, skills)
