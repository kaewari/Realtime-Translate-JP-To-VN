# Walkthrough — Realtime Translate JP To VN

> **Trạng thái: skeleton** (2026-08-06). Các phần "điền khi code landing" sẽ được hoàn thiện theo từng phase trong `plan/plan-2026-08-05-realtime-translate-jp-to-vn.md`.

## Cấu trúc thư mục

Điền khi code landing — xem `README.md` + `wiki/topics/repo-layout.md`.

## Kiến trúc audio pipeline

```
micro ──▶ VAD ──▶ chunk 1–2s ──▶ ASR (ja) ──▶ sentence buffer ──▶ MT (ja→vi) ──▶ WebSocket {ja, vi}
```

- **Capture**: sounddevice (Python) — microphone input
- **VAD**: loại khoảng im lặng, gate cho ASR
- **Chunking**: 1–2 giây/chunk (whisper.cpp streaming hoặc mlx-whisper)
- **ASR**: whisper.cpp (Metal) hoặc mlx-whisper — `language: ja`, model `small`/`medium` (24GB RAM đủ chạy song song ASR + MT)
- **Sentence buffer**: nối fragment thành câu hoàn chỉnh trước khi dịch (tránh dịch vụn, giảm độ trễ cảm nhận)
- **Translation**: Helsinki-NLP/opus-mt-ja-vi (MarianMT, MPS) — nhỏ, chuyên JA→VI, đủ cho MVP; nâng cấp M2M100-418M / NLLB-600M khi cần chất lượng
- **Delivery**: WebSocket — frame `{ja, vi}` đến UI realtime

Vì máy **không có CUDA**: ASR chạy qua **Metal** (whisper.cpp) hoặc **MLX** (mlx-whisper), MT chạy qua **MPS** (PyTorch). faster-whisper (CTranslate2) chỉ chạy CPU trên Mac — dùng được nhưng không tối ưu nhất.

## Luồng xử lý cốt lõi

Điền khi code landing. Dự kiến cover:

- Streaming chunk → ASR → text tạm
- Sentence buffer: gộp fragment → câu (trước khi dịch)
- Latency budget: chunk 1–2s + ASR ~1–2s + MT ~0.5s ≈ vài giây end-to-end (near real-time)
- Edge cases: im lặng đầu/cuối, pause giữa câu, giọng nói xen lẫn tiếng ồn

## Incidents

| Ngày | Sự cố | Nguyên nhân gốc | Fix | Ver |
|---|---|---|---|---|
| — | *(trống)* | | | |

**Quy ước:** mọi lỗi runtime/build/test → append `ERROR:bridge:<msg>` vào `local-bridge/errors.log` (AGENTS §6).
