# Wiki Log

## [2026-08-06] ingest | AGENTS §1a agent branches + local master sync

- AGENTS: agent code trên `{agent}/dev`; plan phase xong → push branch đó; plan tổng xong → `master` rồi sync mọi `*/dev`.
- Plan tổng A+B+C closed → commit `d2df5e8` trên `master`; local sync: `claude/dev`, `cursor/dev`, `deepseek/dev`, `antigravity/dev` = `master`.
- **Chưa có `git remote`** — chưa push; user thêm `origin` rồi `git push -u origin master` + push các `*/dev`.

## [2026-08-06] query | Phase B verified closed (Cursor disk)

- User: plan B đã xong. Disk check: B1 copy UI · B2 `testdata/audio/konnichiwa-16k.wav` · B3 mock+fixture tests · B4 5/5 SKILL.md · B5 README không skeleton · B6 không `allow_credentials` · 8/8 tests OK.
- Plan A/B mốc đóng; wiki Active → **A+B+C closed**.

## [2026-08-06] ingest | Phase B B1–B6 shipped — chờ Cursor/Bugbot verify

- B1 copy buttons: ⧉ per card JA/VI (event delegation) + ⧉ Copy copy-all mỗi panel (`data-item` loại card hệ thống); clipboard API + execCommand fallback, ✓ 1.5s.
- B2 golden audio `testdata/audio/konnichiwa-16k.wav` (say Kyoko + ffmpeg, 16k mono, gitignored) — mlx-whisper ra đúng `こんにちは`.
- B3 ASR test tách: mock pipe unit nhanh + integration fixture thật (skip nếu thiếu wav, kèm lệnh regen). Suite 25.5s → 1.4s.
- B4 3 SKILL.md viết đủ: `skills/local-bridge`, `skills/realtime-translate`, `skills/realtime-regression` — 5/5 skill.
- B5 README sync: bỏ "(đang skeleton)" cho walkthrough; phase-table row 3/4 → ✅ done.
- B6 CORS: bỏ `allow_credentials=True` (combo với `*` vô hiệu) trong `main.py`.
- Tests: 8/8 pass (1.4s) + smoke /health + /api/status + served UI có nút copy. Plan ticked B1–B6 + mốc Phase B. Gate verify: user chạy Cursor/Bugbot.

## [2026-08-06] lint | Continue Phase C — wiki status synced closed

- Cursor re-check: `import mlx_whisper` OK; `load_model` → `mlx-whisper-small-mlx`; unittest 8/8 (~1.9s).
- `wiki/index.md` + topic status: C open → **C closed** (khớp plan continue + living + log đo ~65.7ms).

## [2026-08-06] ingest | Continue Phase C Cursor plan saved under plan/

- Thêm `plan/plan-2026-08-06-continue-phase-c.md` (mirror Cursor Continue Phase C; todos + steps).
- Living checklist vẫn ở `plan/plan-2026-08-06-phase4-latency.md` (cross-link).

## [2026-08-06] ingest | Phase C (latency) verified & closed

- `mlx_whisper` installed successfully trên máy có python3 local. Load time ~4.6s.
- `benchmark_asr.py` avg latency đo được: ~65.7ms per 2s window (vượt xa mục tiêu <1-2s).
- Unit tests (`tests.test_pipeline`) passed xanh. API status badge hiện `mlx-whisper-small-mlx`.
- Reticked Phase C living plan (`plan-2026-08-06-phase4-latency.md`) và plan Continue C. Đã đóng Phase C.

## [2026-08-06] ingest | Continue Phase C plan saved (verify + close)

- Living C cập nhật: `plan/plan-2026-08-06-phase4-latency.md` — reopen checklist đo/đóng; gate nới A-done (B deferred); bảng Số đo trống; appendix handoff Continue C.
- Reality: mlx code + requirements landed; Cursor check thiếu `mlx_whisper` import → mock; claim ~63ms chưa khóa.
- Out of scope đợt này: Phase B, whisper.cpp thứ hai.

## [2026-08-06] ingest | Split plan A/B vs C

- Combined living plan → stub SUPERSEDED: `plan/plan-2026-08-06-bugfix-and-phase4-realtime-translate.md` (giữ filename, không 404).
- Living A/B: `plan/plan-2026-08-06-bugfix-phase-a-b.md` (A1–A6, B1–B6, prompts A/B/Verify; free-claude-code / Flash).
- Living C: `plan/plan-2026-08-06-phase4-latency.md` (latency whisper.cpp/MLX; Antigravity Gemini 3.1 Pro High — không Flash / free-claude-code).
- Wiki Active + topic links cập nhật; code chưa implement.

## [2026-08-06] ingest | Plan AI routing rewrite — prompts A/B/C + Verify

- Living plan in-place: `plan/plan-2026-08-06-bugfix-and-phase4-realtime-translate.md`.
- Assignment: A+B → free-claude-code (DeepSeek V4 Flash); C → Antigravity Gemini 3.1 Pro High; verify sau A/B → Cursor/Bugbot; alternate A/B → Gemini 3.6 Flash High.
- Appendix: Prompt A, Prompt B, Prompt C, Prompt Verify (ready to paste).
- Code chưa implement — mốc A/B/C vẫn open.

## [2026-08-06] ingest | Phase A plan saved — locked fixes + DeepSeek handoff

- Living plan cập nhật in-place: `plan/plan-2026-08-06-bugfix-and-phase4-realtime-translate.md` (sync từ Cursor Phase A plan + Bugbot 5 findings).
- Locked: A1 `asyncio.to_thread`; A4 resample trước `add_float32`; executor DeepSeek V4 Flash; thứ tự A1→A3→A2→A5→A4→A6; appendix handoff prompt.
- Checkbox A1–A6 + mốc Phase A vẫn open — chưa implement.

## [2026-08-06] ingest | Bugcheck review + plan bugfix — Realtime Translate JP To VN

- Bugcheck (`review/codebase-bugcheck-2026-08-06.md`): 7/7 tests pass (20.4s); **P0 confirmed đo thực tế** — WS handler blocking chặn event loop, /health treo 23.6s trong lúc ASR; P1: partial cards không dọn sạch, feedback mic→loa, sample_rate không được đọc, ASR retry load mỗi window + fallback mock âm thầm.
- Plan mới (`plan/plan-2026-08-06-bugfix-and-phase4-realtime-translate.md`): Phase A bugfix P0/P1 → Phase B gap+docs (copy button, golden audio, 3 SKILL.md, README) → Phase C Phase 4 latency (future). Plan cũ 2026-08-05 đánh dấu SUPERSEDED.
- Chưa fix gì — plan mới là kế hoạch, đang chờ implement.

## [2026-08-06] verify | Realtime Translate JP To VN — review claims verified on real hardware

- Verify review trên máy thật: 7/7 tests, ASR thật (whisper-small, MPS 5.8s), MT thật (MarianMT opus-mt-ja-vi), dict fast-path, E2E WS với audio thật.
- Fix scipy: pin `scipy==1.14.1` (wheel 1.15+ fail dyld macOS 27 trên cp310 → ASR fallback mock âm thầm).
- Fix contract `is_final`: server resend partial cuối kèm `is_final=true` khi flush rỗng; UI gửi `is_final` khi stop + replace card cuối (dedupe).
- `asr_device` default chuyển `cpu` → `mps` (fallback cpu nếu không có MPS).
- Open gaps: UI thiếu nút copy text (review nói có); latency ASR ~5.8s/window → Phase 4 (whisper.cpp/MLX) chưa làm; streaming hallucination trên chunk giữa câu (MVP chấp nhận).
- Raw: plan header cập nhật theo reality; review/ giữ nguyên (bất biến).

## [2026-08-06] ingest | Phase A A1–A6 shipped — chờ Cursor/Bugbot verify

- A1 to_thread (P0 event-loop blocking); A2 partial-group dọn card; A3 GainNode 0 hết feedback; A4 sample_rate contract + numpy resample 16k (smoke 48k: 1 WARNING/session); A5 load_failed + engine badge; A6 dead code + confidence Optional + dict strip dấu câu.
- Smoke: /health 3ms khi WS transcribe; 48k chunk → pipeline vẫn trả kết quả. 7/7 tests pass (25.5s).
- Plan ticked A1–A6 + mốc Phase A `2026-08-06 · verified Cursor/Bugbot: ____`. Gate Phase B chờ user chạy Cursor/Bugbot verify A.
