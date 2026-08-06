# Topic: Realtime Translate JP To VN

## Status
MVP Ready · A+B+C closed · utterance-end verified · D-UI restored (`d9e9b9f`) · **D-UX closed** (S1+S2 verified Cursor 2026-08-06 @ `0593932` — [ux-interaction](../plan/plan-2026-08-06-ux-interaction.md)). mlx ~65.7ms.

## Verified on real hardware (2026-08-06)
- 7/7 unit tests pass (`python3 -m unittest discover -s tests`)
- ASR thật: `mlx-whisper-small-mlx` (`mlx-community/whisper-small-mlx`); load ~4.6s; avg ~65.7ms / 2s noise window (Continue C verify 2026-08-06)
- MT thật: MarianMT `opus-mt-ja-vi` — `今日はとてもいい天気ですね` → `Hôm nay là một ngày đẹp trời.`; dict fast-path ~0.00s
- E2E WebSocket với audio thật (konnichiwa.wav, 2 chunks + flush): `こんにちは。→ Xin chào.` + `is_final=True` được gửi đủ
- UI: dark glassmorphism, Web Audio API → PCM16 base64, meter, latency tag — khớp claim

### ⚠️ Điều kiện chạy (mới phát hiện)
- `scipy==1.14.1` bắt buộc: wheel `scipy>=1.15` cho Python 3.10 fail dyld trên macOS 27 (`__thread_bss` zero-fill trong `_spropack`) → transformers pipeline crash → ASR âm thầm fallback mock. Đã pin trong `local-bridge/requirements.txt`.

## Fixes shipped 2026-08-06 (sau review)
- **Contract `is_final` đã đóng**: trước đây flush rỗng → server không bao giờ gửi `is_final=true`; giờ [endpoints.py](file:///Users/hoangson/Documents/Realtime%20Translate%20JP%20To%20VN/local-bridge/app/api/endpoints.py) lưu partial cuối và resend kèm `is_final=true` khi flush không có audio mới. UI gửi `is_final:true` khi stopRecording và replace card cuối (dedupe) thay vì append trùng.

## Phase A shipped 2026-08-06 (A1–A6, plan ticked — chờ Cursor/Bugbot verify)
- **A1 (P0)**: `asyncio.to_thread` quanh ASR/MT (WS audio, WS text, REST) — /health 3ms khi WS đang transcribe (smoke: mock sleep 2s).
- **A2**: `data-partial-group` — final xóa cả nhóm partial rồi append 1 card; reset group khi mic start / gửi text.
- **A3**: `GainNode gain=0` thay connect destination — hết feedback mic→loa, meter vẫn chạy.
- **A4**: client gửi `sample_rate`; server WARNING 1 lần/session + numpy linear interp về 16k trước `add_float32` (smoke 48k: 1 WARNING/session, pipeline vẫn trả kết quả).
- **A5**: `load_failed` — không retry load mỗi window; `engine_name="fallback-asr (load failed)"`; UI badge `ASR: … · MT: …` từ GET /api/status.
- **A6**: xóa `filter_silence`, `AudioChunkMessage`, `chunk_duration_sec`, `min_speech_duration_sec`, `silence_count`; `confidence: Optional[float]=None` (hết hardcode 0.95/1.0/0.8); `itemCounter` chỉ tăng khi final; dict fast-path strip `。、！？`.
- Tests: 7/7 pass (25.5s). Chi tiết từng fix: [plan-2026-08-06-bugfix-phase-a-b.md](../plan/plan-2026-08-06-bugfix-phase-a-b.md).

## Bugcheck 2026-08-06 (`review/codebase-bugcheck-2026-08-06.md`) — P0/P1 đã fix Phase A, chờ verify
- **P0 [đo thực tế]**: WS handler gọi ASR/MT blocking trên event loop → GET /health trong lúc WS ASR **treo 23.6s**. Fix: `asyncio.to_thread` hoặc sync handler.
- **P1**: UI chỉ xóa card partial cuối khi finalize → utterance nhiều window để lại partial giữa câu (`web/index.html:477-482`).
- **P1**: `scriptProcessor.connect(destination)` phát mic ra loa → feedback loop (`web/index.html:553-554`).
- **P1**: `sample_rate` không được server đọc — browser 44.1k/48k → ASR nghe sai.
- **P1**: ASR retry `load_model` mỗi window khi fail (spam errors.log — 3 WARNING trùng) + fallback mock âm thầm, UI không có engine badge.
- P2: dead code (`filter_silence`, `AudioChunkMessage`, 2 config field, `silence_count`), `confidence` hardcode, `itemCounter` đếm cả partial, CORS `*`+credentials, dict miss dấu câu `。`, MT `load_model` race.
- Docs: README:72 nói walkthrough "(đang skeleton)" — sai; 3/5 skill thiếu SKILL.md; `testdata/` trống; `test_asr_service` chạy whisper thật (~18s/20.4s suite).
- Kế hoạch: [A/B](../plan/plan-2026-08-06-bugfix-phase-a-b.md) · [C living](../plan/plan-2026-08-06-phase4-latency.md) · [C continue](../plan/plan-2026-08-06-continue-phase-c.md) (gate nới A-done). Combined cũ → [SUPERSEDED stub](../plan/plan-2026-08-06-bugfix-and-phase4-realtime-translate.md).

## Phase B shipped 2026-08-06 (B1–B6 — verified Cursor disk 2026-08-06)
- **B1**: nút copy ⧉ per card (JA + VI, event delegation trên `jaList`/`viList`) + `⧉ Copy` copy-all mỗi panel (`data-item` loại card hệ thống); clipboard API + execCommand fallback, feedback ✓ 1.5s.
- **B2**: golden `testdata/audio/konnichiwa-16k.wav` (say Kyoko + ffmpeg 16k mono, gitignored) — mlx-whisper transcribe ra đúng `こんにちは`.
- **B3**: `test_asr_service` → mock pipe (fast unit, kiểm tra language/task contract); thêm integration test fixture thật (skip nếu thiếu wav kèm lệnh regen). Suite 25.5s → 1.4s.
- **B4**: viết `skills/local-bridge/SKILL.md`, `skills/realtime-translate/SKILL.md`, `skills/realtime-regression/SKILL.md` — 5/5 skill đủ.
- **B5**: README dòng "walkthrough (đang skeleton)" → đầy đủ; phase-table row 3/4 sync reality (nút copy, mlx-whisper done).
- **B6**: bỏ `allow_credentials=True` (combo với `*` vô hiệu) trong `main.py`.
- Tests: **8/8 pass (1.4s)** + smoke /health + /api/status + served UI có nút copy.

## Open gaps
- **Latency ASR**: Phase C **closed** — ~65.7ms/window (mlx); xem [plan C](../plan/plan-2026-08-06-phase4-latency.md).
- **Utterance jump / mid-sentence ASR**: **verified closed 2026-08-06** — `pop_utterance` silence endpointing (0.6s/8.0s/0.4s) thay greedy `get_window` [utterance-endpointing](../plan/plan-2026-08-06-utterance-endpointing.md); Cursor disk + 11/11 tests.
- Copy text: **đã đóng** bởi B1 (per card + copy all).
- **D-UX Sprint 1**: **verified closed** — mic / export / edit JA / Space / offline ([ux-interaction](../plan/plan-2026-08-06-ux-interaction.md)).
- **D-UX Sprint 2**: **verified closed** Cursor 2026-08-06 @ `0593932` — PiP (`documentPictureInPicture`), localStorage restore, TTS VI (`.speak-btn` + `cancel()`), `manifest.json` + `icon.svg` (no SW). Plan D-UX đóng.
- **D-UI**: **restored** trên `antigravity/dev` @ `d9e9b9f` (UI1–4 + is_final) — [restore](../plan/plan-2026-08-06-restore-d-ui.md) · [ui-visual](../plan/plan-2026-08-06-ui-visual.md).

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
- Plan (closed utterance-end, verified Cursor): [plan-2026-08-06-utterance-endpointing.md](file:///Users/hoangson/Documents/Realtime%20Translate%20JP%20To%20VN/plan/plan-2026-08-06-utterance-endpointing.md)
- Plan (closed A/B): [plan-2026-08-06-bugfix-phase-a-b.md](file:///Users/hoangson/Documents/Realtime%20Translate%20JP%20To%20VN/plan/plan-2026-08-06-bugfix-phase-a-b.md)
- Plan (active C living): [plan-2026-08-06-phase4-latency.md](file:///Users/hoangson/Documents/Realtime%20Translate%20JP%20To%20VN/plan/plan-2026-08-06-phase4-latency.md)
- Plan (Continue C snapshot): [plan-2026-08-06-continue-phase-c.md](file:///Users/hoangson/Documents/Realtime%20Translate%20JP%20To%20VN/plan/plan-2026-08-06-continue-phase-c.md)
- Plan (stub SUPERSEDED): [plan-2026-08-06-bugfix-and-phase4-realtime-translate.md](file:///Users/hoangson/Documents/Realtime%20Translate%20JP%20To%20VN/plan/plan-2026-08-06-bugfix-and-phase4-realtime-translate.md) (split 2026-08-06)
- Plan (closed): [plan-2026-08-05-realtime-translate-jp-to-vn.md](file:///Users/hoangson/Documents/Realtime%20Translate%20JP%20To%20VN/plan/plan-2026-08-05-realtime-translate-jp-to-vn.md) (SUPERSEDED 2026-08-06; header cập nhật: scipy pin, MPS default, is_final fix)
- Review: [review-realtime-translate-implementation-2026-08-06.md](file:///Users/hoangson/Documents/Realtime%20Translate%20JP%20To%20VN/review/review-realtime-translate-implementation-2026-08-06.md) (bất biến — findings đã phản ánh vào plan/wiki)
- Review: [codebase-bugcheck-2026-08-06.md](file:///Users/hoangson/Documents/Realtime%20Translate%20JP%20To%20VN/review/codebase-bugcheck-2026-08-06.md) (bất biến — bugcheck P0/P1, chưa fix)
