# Wiki Log

## [2026-08-06] verify | Realtime Translate JP To VN — review claims verified on real hardware

- Verify review trên máy thật: 7/7 tests, ASR thật (whisper-small, MPS 5.8s), MT thật (MarianMT opus-mt-ja-vi), dict fast-path, E2E WS với audio thật.
- Fix scipy: pin `scipy==1.14.1` (wheel 1.15+ fail dyld macOS 27 trên cp310 → ASR fallback mock âm thầm).
- Fix contract `is_final`: server resend partial cuối kèm `is_final=true` khi flush rỗng; UI gửi `is_final` khi stop + replace card cuối (dedupe).
- `asr_device` default chuyển `cpu` → `mps` (fallback cpu nếu không có MPS).
- Open gaps: UI thiếu nút copy text (review nói có); latency ASR ~5.8s/window → Phase 4 (whisper.cpp/MLX) chưa làm; streaming hallucination trên chunk giữa câu (MVP chấp nhận).
- Raw: plan header cập nhật theo reality; review/ giữ nguyên (bất biến).
