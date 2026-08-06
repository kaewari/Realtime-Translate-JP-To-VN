# Topic: Realtime Translate JP To VN

## Status
MVP Ready + **đã verify trên máy thật** (2026-08-06 tối) · Bugcheck 2026-08-06: P0/P1 xác nhận, plan fix mới lập (chưa implement)

## Verified on real hardware (2026-08-06)
- 7/7 unit tests pass (`python3 -m unittest discover -s tests`)
- ASR thật: whisper-small, `こんにちは` → đúng; MPS ~5.8s / CPU ~8.2s (first call ~12s do lazy-load model)
- MT thật: MarianMT `opus-mt-ja-vi` — `今日はとてもいい天気ですね` → `Hôm nay là một ngày đẹp trời.`; dict fast-path ~0.00s
- E2E WebSocket với audio thật (konnichiwa.wav, 2 chunks + flush): `こんにちは。→ Xin chào.` + `is_final=True` được gửi đủ
- UI: dark glassmorphism, Web Audio API → PCM16 base64, meter, latency tag — khớp claim

### ⚠️ Điều kiện chạy (mới phát hiện)
- `scipy==1.14.1` bắt buộc: wheel `scipy>=1.15` cho Python 3.10 fail dyld trên macOS 27 (`__thread_bss` zero-fill trong `_spropack`) → transformers pipeline crash → ASR âm thầm fallback mock. Đã pin trong `local-bridge/requirements.txt`.

## Fixes shipped 2026-08-06 (sau review)
- **Contract `is_final` đã đóng**: trước đây flush rỗng → server không bao giờ gửi `is_final=true`; giờ [endpoints.py](file:///Users/hoangson/Documents/Realtime%20Translate%20JP%20To%20VN/local-bridge/app/api/endpoints.py) lưu partial cuối và resend kèm `is_final=true` khi flush không có audio mới. UI gửi `is_final:true` khi stopRecording và replace card cuối (dedupe) thay vì append trùng.

## Bugcheck 2026-08-06 (`review/codebase-bugcheck-2026-08-06.md`) — đang mở, chưa fix
- **P0 [đo thực tế]**: WS handler gọi ASR/MT blocking trên event loop → GET /health trong lúc WS ASR **treo 23.6s**. Fix: `asyncio.to_thread` hoặc sync handler.
- **P1**: UI chỉ xóa card partial cuối khi finalize → utterance nhiều window để lại partial giữa câu (`web/index.html:477-482`).
- **P1**: `scriptProcessor.connect(destination)` phát mic ra loa → feedback loop (`web/index.html:553-554`).
- **P1**: `sample_rate` không được server đọc — browser 44.1k/48k → ASR nghe sai.
- **P1**: ASR retry `load_model` mỗi window khi fail (spam errors.log — 3 WARNING trùng) + fallback mock âm thầm, UI không có engine badge.
- P2: dead code (`filter_silence`, `AudioChunkMessage`, 2 config field, `silence_count`), `confidence` hardcode, `itemCounter` đếm cả partial, CORS `*`+credentials, dict miss dấu câu `。`, MT `load_model` race.
- Docs: README:72 nói walkthrough "(đang skeleton)" — sai; 3/5 skill thiếu SKILL.md; `testdata/` trống; `test_asr_service` chạy whisper thật (~18s/20.4s suite).
- Kế hoạch fix: [plan-2026-08-06-bugfix-and-phase4-realtime-translate.md](../plan/plan-2026-08-06-bugfix-and-phase4-realtime-translate.md) — Phase A (bugfix, đang mở) → Phase B (copy button, golden audio, SKILL.md, README) → Phase C (Phase 4 latency, future).

## Open gaps
- **Copy text**: review nói UI có nút copy — thực tế chưa có (chỉ Start/Stop, Dịch, Xóa). Đã lên Phase B.1 của plan mới.
- **Latency ASR**: ~5.8s/window trên MPS (transformers) — realtime là "near". Phase 4 plan: whisper.cpp/MLX để xuống dưới ~1-2s.
- **Streaming hallucination**: chunk giữa câu có thể ra text sai (`コンニング`); MVP chấp nhận, câu cuối luôn đúng qua `is_final`.

## System Overview
Hệ thống dịch tiếng Nhật sang tiếng Việt thời gian thực (near real-time), hoạt động hoàn toàn cục bộ (local-first) trên Apple Silicon Mac M5 Pro.

## Core Code Anchors
- **Entrypoint**: [main.py](file:///Users/hoangson/Documents/Realtime%20Translate%20JP%20To%20VN/local-bridge/app/main.py)
- **API & WebSocket Routes**: [endpoints.py](file:///Users/hoangson/Documents/Realtime%20Translate%20JP%20To%20VN/local-bridge/app/api/endpoints.py)
- **VAD Service**: [vad_service.py](file:///Users/hoangson/Documents/Realtime%20Translate%20JP%20To%20VN/local-bridge/app/services/vad_service.py)
- **ASR Service**: [asr_service.py](file:///Users/hoangson/Documents/Realtime%20Translate%20JP%20To%20VN/local-bridge/app/services/asr_service.py)
- **Translation Service**: [translation_service.py](file:///Users/hoangson/Documents/Realtime%20Translate%20JP%20To%20VN/local-bridge/app/services/translation_service.py)
- **Audio Buffer**: [audio_buffer.py](file:///Users/hoangson/Documents/Realtime%20Translate%20JP%20To%20VN/local-bridge/app/services/audio_buffer.py)
- **Web UI**: [index.html](file:///Users/hoangson/Documents/Realtime%20Translate%20JP%20To%20VN/web/index.html)
- **Test Suite**: [test_pipeline.py](file:///Users/hoangson/Documents/Realtime%20Translate%20JP%20To%20VN/local-bridge/tests/test_pipeline.py)

## Raw Sources
- Plan (active): [plan-2026-08-06-bugfix-and-phase4-realtime-translate.md](file:///Users/hoangson/Documents/Realtime%20Translate%20JP%20To%20VN/plan/plan-2026-08-06-bugfix-and-phase4-realtime-translate.md)
- Plan (closed): [plan-2026-08-05-realtime-translate-jp-to-vn.md](file:///Users/hoangson/Documents/Realtime%20Translate%20JP%20To%20VN/plan/plan-2026-08-05-realtime-translate-jp-to-vn.md) (SUPERSEDED 2026-08-06; header cập nhật: scipy pin, MPS default, is_final fix)
- Review: [review-realtime-translate-implementation-2026-08-06.md](file:///Users/hoangson/Documents/Realtime%20Translate%20JP%20To%20VN/review/review-realtime-translate-implementation-2026-08-06.md) (bất biến — findings đã phản ánh vào plan/wiki)
- Review: [codebase-bugcheck-2026-08-06.md](file:///Users/hoangson/Documents/Realtime%20Translate%20JP%20To%20VN/review/codebase-bugcheck-2026-08-06.md) (bất biến — bugcheck P0/P1, chưa fix)
