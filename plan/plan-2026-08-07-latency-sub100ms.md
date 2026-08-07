<!-- date: 2026-08-07 -->
<!-- source: chat:latency-realtime-review · user: tối ưu phản hồi <100ms đo từ lúc nói xong -->

# Plan: Latency <100ms (speech-end → final response) — Realtime Translate JP To VN

## Mốc đo (user xác nhận 2026-08-07)

**Âm cuối dừng (last speech sample) → bản dịch final hiện ra ≤ 100ms.**

Không thể đạt nếu giữ kiến trúc cũ: chờ im lặng 0.6s + chạy lại ASR+MT khi có kết quả
(`audio_buffer.pop_utterance` chỉ emit sau 0.6s silence / 8s / flush; mọi response `is_final=true`).

## Thiết kế (ponytail — tận dụng tối đa code đã có)

### Nguyên lý: decode liên tục + final lạc quan (optimistic final)

1. **Streaming partials**: mỗi chunk speech đến (chunk 1024 @16k = 64ms), nếu
   `total_speech >= min_speech_sec` và có audio mới kể từ lần decode trước
   (`partial_step_sec`), decode window hiện tại (mlx ~15-65ms) → gửi
   `is_final=false` + `utterance_id` (JA+VI).
2. **Final không chờ**: khi chunk silence đầu tiên sau speech
   (`trailing_silence >= endpoint_silence_sec`, mặc định 1 chunk = 64ms):
   gửi final = **kết quả partial cuối đã decode sẵn** (không chạy lại ASR/MT →
   chi phí ≈ send chỉ vài ms). Latency ≈ 1 chunk + send ≈ 70-90ms.
3. **Sửa sai khi nói lại** (`resume_grace_sec`, mặc định 0.4s): nói tiếp trong
   grace → decode lại window (gồm audio mới), gửi partial cập nhật cùng
   `utterance_id` rồi final mới **cùng id** → UI thay card cũ bằng card mới
   (không tăng counter lần 2). Ngược lại, nói tiếp sau grace → utterance mới.
4. **Flush (stopRecording)** vẫn gửi final ngay với kết quả đã có.
5. **max_utterance_sec 8s** giữ nguyên (partials đã che phủ nói liên tục).

### Latency thật (không cần clock sync)

Server biết `last_speech_ts` (thời điểm nhận chunk speech cuối + hết chunk đó).
`latency_ms = (now - last_speech_ts) * 1000` tại lúc send final → đo đúng
"nói xong → phản hồi". Client không cần đổi đồng hồ.

### Client (web/index.html)

- `createScriptProcessor(4096)` → `(1024)`; thêm `t0`/send ts không cần (server tự đo).
- Partial: **replace 1 live card** của utterance hiện tại (không prepend card mới mỗi partial).
- Final: thẻ mang `data-utterance`; khi final cùng id → thay thẻ cũ, không tăng counter lần 2;
  nhóm cleanup theo `partialGroup` giữ nguyên.

### Config

| Field | Giá trị mới | Ý nghĩa |
|---|---|---|
| `endpoint_silence_sec` | `0.064` (1 chunk 1024) | phát final ngay chunk silence đầu |
| `resume_grace_sec` | `0.4` | thời gian cho phép nói lại cùng utterance |
| `partial_step_sec` | `0.25` | cadence decode partial tối thiểu |
| `min_speech_sec` | `0.4` | giữ nguyên — không decode trước đủ speech |

### Các thay đổi code

- `app/core/config.py`: `endpoint_silence_sec=0.064`, thêm `resume_grace_sec`, `partial_step_sec`.
- `app/services/audio_buffer.py`: thêm `partial_window()` (copy không reset), `last_speech_ts`,
  `should_emit_final()`; `pop_utterance(flush)` giữ nguyên cho confirm/reset; reset buffer khi
  speech mới sau grace.
- `app/api/endpoints.py`: vòng lặp streaming (decode partial mỗi chunk có cadence; final lạc
  quan; corrected final cùng utterance_id; flush path; `latency_ms` từ `last_speech_ts`).
- `web/index.html`: chunk 1024, live partial card, `data-utterance` replace, hiển thị latency thật.
- `benchmark_latency_e2e.py`: gửi wav theo nhịp realtime (64ms/chunk) + silence chunk; đo
  speech-end→final p50/p95 (lặp N lần).

## Điều kiện chấp nhận (Definition of Done)

- [ ] E2E benchmark: **p50 ≤ 100ms, p95 ≤ ~150ms** (speech-end → final nhận tại client).
- [ ] Partial hiện khi đang nói (mỗi ~0.25s có cập nhật, `is_final=false`).
- [ ] Nói lại trong grace → thẻ cập nhật (không card trùng, counter không tăng 2).
- [ ] `python3 -m unittest tests.test_pipeline` xanh (có test mới cho partial/optimistic final).
- [ ] `/api/status` engine không đổi (mlx-whisper-small-mlx, MarianMT).
- [ ] UI mở http://localhost:8766/ dùng được, latency tag hiện số thật.

## Out of scope

- AudioWorklet (chunk 1024 giữ ScriptProcessor — đủ cho mục tiêu; worklet là bước sau).
- Đổi model ASR/MT (giữ small + MarianMT; chỉ đổi nếu benchmark không đạt — mục
  "model nhỏ hơn" mở lại nếu cần).
- Whisper.cpp / binary WS.

## Executor

opencode (deepseek) — task branch `latency-100/dev` → merge `antigravity/dev` khi xong.
