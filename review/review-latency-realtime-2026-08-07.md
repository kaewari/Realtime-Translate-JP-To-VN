<!-- date: 2026-08-07 -->
<!-- source: chat:latency-realtime-review · user: realtime nhưng tốc độ phản hồi quá chậm — đọc source, nêu tối ưu + bug -->

# Review: Latency & Bug Realtime Pipeline (2026-08-07)

## Kết luận ngắn

Pipeline hiện tại **không phải realtime khi đang nói**: kết quả chỉ được emit sau khi hết câu
(im lặng ≥ 0.6s) hoặc chạm 8s, mọi response đều `is_final=true`, không có partial. Độ trễ
cảm nhận = cuối câu + 0.6s + ASR + MT + queue. Số đo `~63ms` trong wiki chỉ là **ASR warm
trên noise**, không phải E2E.

Phân loại: **P0** = thay đổi kiến trúc để có phản hồi khi đang nói · **P1** = bug làm sai
kết quả/mất audio · **P2** = tối ưu nhỏ. File/line dẫn đúng source hiện tại (đã re-read disk).

---

## P0 — Kiến trúc chặn "realtime khi đang nói"

### P0-1. Không có partial — phản hồi chỉ sau khi dừng nói (tối đa 8s)

- `pop_utterance()` chỉ trả audio khi: silence ≥ 0.6s sau speech ≥ 0.4s, hoặc buffer ≥ 8s,
  hoặc flush — `local-bridge/app/services/audio_buffer.py:58-85`.
- WS chỉ gửi kết quả khi `pop_utterance` trả về, và luôn đặt `is_final=True` —
  `local-bridge/app/api/endpoints.py:106-126`.
- Nói liên tục → kết quả đầu tiên trễ tới `max_utterance_sec = 8.0` — `app/core/config.py:18-21`.

UI **đã có sẵn cơ chế partial** (`data-partial-group`, xóa group khi final) nhưng server
không bao giờ gửi `is_final=false` → cơ chế đó thành dead code — `web/index.html:654-697`.

**Hướng fix:** rolling-window partial: cứ mỗi ~1s, transcribe window trượt, gửi `is_final=false`
kèm `utterance_id` (server cấp); khi silence-endpoint/flush gửi `is_final=true` cùng id. UI
đã sẵn sàng thay card cùng group.

### P0-2. Xử lý tuần tự chặn nhận audio — backlog + stop-final trễ

- Trong 1 vòng lặp: `receive_text → buffer → await ASR(to_thread) → await MT(to_thread) → send` —
  `endpoints.py:65-126`. Trong lúc chờ inference, server **không gọi `receive_text()`**:
  message WS do framework đệm lại (tăng memory), client không hề biết → cứ gửi tiếp.
- Client không kiểm tra `ws.bufferedAmount` — `web/index.html:869-875`.
- Hệ quả: khi ASR lâu (cold load ~20s đầu, hoặc burst), audio chồng backlog; flush (stop)
  bị trễ theo; nguy cơ socket/queue đầy mất audio.

**Hướng fix tối thiểu:** tách reader/worker — vòng loop chỉ nhận + đẩy audio vào bounded
queue (`asyncio.Queue(maxsize=N)`); worker consume để ASR/MT; khi queue đầy → drop/merge
audio cũ (chấp nhận mất, không tích lũy); client dừng gửi khi `bufferedAmount` > ngưỡng.

### P0-3. `latency_ms` không phản ánh độ trễ thật

- Timer bắt đầu **sau** khi nhận xong message — `endpoints.py:67`; không tính capture,
  chờ endpointing, network, render UI.
- Khi flush rỗng, gửi lại `last_result` với **latency cũ** — `endpoints.py:127-138`.
- → mọi con số hiển thị "Độ trễ: Nms" trên UI là giả, không dùng để debug được.

**Hướng fix:** client gửi `client_ts` (performance.now) trong mỗi chunk; server phản hồi kèm
`latency_ms = receive_time - client_ts` (+ stage timings: receive/decode/endpoint/ASR/MT/send).

---

## P1 — Bug làm sai kết quả / mất audio

### P1-1. Duplicate/stale final khi stop (confirm đọc code)

`last_result` sống suốt session — `endpoints.py:61,125,127-138`:

1. VAD tự emit final → user bấm stop khi buffer rỗng → server **resend đúng kết quả cũ** như
   final mới → UI thêm card trùng + tăng counter — `index.html:654-660`.
2. Start lại, chỉ có silence → buffer rỗng → resend kết quả utterance trước (stale).

**Fix:** clear `last_result` sau khi đã dùng 1 lần; chỉ resend khi có kết quả mới kể từ lần
emit gần nhất; tốt hơn: bỏ luôn nhánh resend khi endpoint đã tự gửi final (P0-1).

### P1-2. VAD theo chunk-tail có thể nuốt mất đầu câu

- Chỉ xét 200ms cuối chunk — `audio_buffer.py:46-56`. Chunk 4096 mẫu @16k = 256ms; khi
  resample từ 48k, chunk sau resample < 200ms → cả chunk bị xét bằng đuôi → speech đầu
  chunk tính thành silence, bị trim khi endpoint (`audio_buffer.py:73`).
- Max-cap cắt tại 8s với `overlap=0` → từ bị cắt đôi giữa chừng (`audio_buffer.py:78-84`).

**Fix:** VAD trên toàn chunk (hoặc tách segment speech/silence trong chunk), trim silence
từng mẫu; max-cap giữ overlap ~0.5s context cho ASR.

### P1-3. Hallucination & fake transcript lẫn vào kết quả thật

- Flush gửi **mọi buffer non-empty kể cả toàn silence** vào Whisper — `audio_buffer.py:65-68`
  (không check `min_speech_sec` như nhánh thường). Whisper dễ hallucinate trên silence/tail
  noise — lịch sử `errors.log` có `ご視聴ありがとうございました`; bộ lọc `_filter_whisper_junk`
  chỉ loại đúng 3 chuỗi cố định — `asr_service.py:7-17`.
- Khi ASR fail, **mọi audio không im lặng** trả câu giả cố định `こんにちは、リアルタイム翻訳テストです。`
  với `confidence=None` (trông như kết quả hợp lệ) — `asr_service.py:80-86`.

**Fix:** flush silence-only → không đưa vào ASR; Whisper set `condition_on_previous_text=False`
giảm hallucination vòng lặp; response thêm cờ `is_fallback` để UI badge.

### P1-4. Model lazy-load race + cold start không kiểm soát

- `asr_service`/`translation_service` là singleton, được gọi đồng thời qua `to_thread` —
  nhiều request đầu có thể load model cùng lúc, ghi đè `is_loaded`/`load_failed` —
  `asr_service.py:27-53`, `translation_service.py:41-60`; không lock, không timeout download.
- `load_failed` sticky → lỗi dependency phải restart mới thử lại — `asr_service.py:51`.
- Cold start lần đầu WS có thể ~20s (weight cache) — trong lúc đó P0-2 tích backlog.

**Fix:** lock (`threading.Lock`) quanh load; warmup model tại startup (không chờ chunk đầu);
UI chỉ bật mic khi engine sẵn sàng (xem P1-6).

### P1-5. Mất audio khi stop/reconnect

- `stopRecording()` đặt `isRecording=false` trước flush → tối đa 1 chunk (256ms) bị bỏ —
  `index.html:900-918`.
- WS mất kết nối → `onclose` gọi `stopRecording()` nhưng socket đã CLOSED → **không gửi
  được flush**, buffer server mất trắng; không có ACK/sequence để reconnect replay —
  `index.html:632-640`.
- Double-click mic trong lúc `startRecording` chưa xong (`isRecording` set sau nhiều await)
  → tạo nhiều stream/AudioContext; cleanup chỉ dọn reference cuối — `index.html:827-898`.

**Fix:** set trạng thái `starting` + disable nút; chờ flush ACK trước khi cho phép start lại;
giữ ring buffer nhỏ client + sequence để replay sau reconnect.

### P1-6. Bật mic khi pipeline chưa sẵn sàng

UI bật `btnMic` ngay khi WS OPEN — `index.html:612-615` — trong khi ASR/MT lazy-load trên
chunk đầu. `/api/status` có thể vẫn `Whisper (Pending)`; badge chỉ cảnh báo khi chuỗi chứa
"fallback"/"mock" — `index.html:589-602`.

**Fix:** tách trạng thái "WS connected" vs "engine ready" (poll `/api/status` hoặc WS event);
disable mic tới khi engine ready.

---

## P2 — Tối ưu nhỏ (sau P0/P1)

| # | Mục | Vị trí |
|---|---|---|
| P2-1 | Chunk 4096 → 1024/2048: giảm lượng tử endpoint (0.6s silence thêm tới +256ms) và mất audio khi stop | `web/index.html:840` |
| P2-2 | `np.concatenate` mỗi chunk = O(n²) khi backlog; giữ list + concat 1 lần lúc emit | `audio_buffer.py:56` |
| P2-3 | MT chạy CPU mặc định; nhánh `mt_device="mps"` có bug: đẩy input lên MPS khi model còn CPU nếu MPS không khả dụng → crash | `translation_service.py:50-53,79-86`, `config.py:29` |
| P2-4 | `ScriptProcessor` deprecated, chạy trên main thread (RMS loop + Int16 + string concat + btoa + JSON + send mỗi callback); sau P0 nên chuyển AudioWorklet | `index.html:842-877` |
| P2-5 | `initAudioDevices()` gọi `getUserMedia` nhưng không stop stream → đèn mic vẫn sáng | `index.html:994-1006` |
| P2-6 | `saveSession()` serialize toàn bộ innerHTML mỗi final, DOM không giới hạn, localStorage đầy throw không bắt | `index.html:699-703,705-718` |
| P2-7 | Logger ghi file đồng bộ trên event loop path | `app/utils/logger.py:8-26` |
| P2-8 | JSON malformed (vd array) làm đóng session — validate shape trước khi xử lý | `endpoints.py:69-75` |

---

## Khoảng trống đo lường (P0-evidence)

- `benchmark_asr.py:23-41` chỉ đo ASR warm trên **random noise 2s**, không qua WS/VAD/
  buffer/MT/network → con số `~63-65.7ms` trong wiki/skill **không phải E2E**.
- Test WS chỉ gửi `event:"text"`, không chạy nhánh audio — `tests/test_pipeline.py:152-158`.
- Chưa có test: audio WS 48k/resample, flush silence, duplicate final, concurrency load,
  backpressure, `to_thread` regression (health probe khi WS đang transcribe).

**Bộ đo tối thiểu cần thêm:** stage timing (receive/decode+resample/endpoint/ASR/MT/send)
+ p50/p95/p99 của capture→UI (client `performance.now`); probe `/health` song song lúc ASR;
2-4 WS đồng thời.

## Docs stale (sửa cùng đợt)

- Số test 7/8/11 khắp wiki/plan/walkthrough trong khi source có 12 methods.
- `walkthrough.md` còn ghi sliding window 1.5-3s — thực tế endpointing 0.6s/8s.
- Skill realtime-translate ghi "MPS ~63ms" — thực tế mlx-whisper, và `asr_device` config không được dùng.

## Thứ tự đề xuất

1. **P0-1** rolling partial + `utterance_id` (server) — tận dụng UI đã có sẵn partial-group.
2. **P0-2** reader/worker + bounded queue + client `bufferedAmount`.
3. **P1-1** clear `last_result` / bỏ resend — fix duplicate ngay.
4. **P1-3** chặn silence flush vào ASR + cờ fallback.
5. **P0-3** `client_ts` → latency thật; rồi mới đo lại E2E để có baseline.
6. P1-4/5/6, P2, docs.
