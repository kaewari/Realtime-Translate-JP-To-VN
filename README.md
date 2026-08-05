# Realtime Translate JP To VN

Dịch giọng nói **tiếng Nhật → tiếng Việt** theo thời gian thực (near real-time), local-first, tối ưu cho Apple Silicon.

> **Trạng thái: scaffold** (2026-08-06) — chỉ có cấu trúc thư mục + AGENTS/skills/wiki. Chưa có code hoạt động.

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
- ASR: **whisper.cpp (Metal)** hoặc **mlx-whisper** — model `small`/`medium`, `language: ja`
- Translation: **Helsinki-NLP/opus-mt-ja-vi** (MarianMT, MPS) → nâng cấp M2M100/NLLB sau
- Audio: **sounddevice** (thu micro) + ffmpeg (xử lý/convert)
- UI: web (MVP: HTML/JS đơn giản, sau có thể Next.js) — sẽ đặt dưới `web/` (TBD)

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

> ⏳ TODO — điền khi backend MVP chạy được (Phase 1).

1. `cd local-bridge && python3.10 -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt` *(chưa có)*
3. `uvicorn app.main:app --port 8765`
4. POST `/bootstrap` → chờ download model → mở UI...

## Lộ trình

| Phase | Nội dung | Trạng thái |
|---|---|---|
| 1 | PoC nhanh — thu micro → ASR → dịch → in text | pending |
| 2 | Near real-time — VAD, chunking, sentence buffer | pending |
| 3 | UI — start/stop, hiển thị JA + VI, timestamp | pending |
| 4 | Tối ưu hiệu năng — Metal/quantization | pending |

Chi tiết: `plan/plan-2026-08-05-realtime-translate-jp-to-vn.md`.

## Docs khác

- `walkthrough.md` — kiến trúc audio pipeline + hướng dẫn chạy (đang skeleton)
- `AGENTS.md` — quy ước bắt buộc cho mọi agent (ponytail, plan/review, wiki, skills)
