# Wiki Log

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
