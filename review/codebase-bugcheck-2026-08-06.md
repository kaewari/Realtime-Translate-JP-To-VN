<!-- date: 2026-08-06 -->
<!-- source: chat:bugcheck-realtime-translate · user: đọc sourcecode, check bug, check plan để viết review và lập plan mới -->

# Review Bugcheck — Realtime Translate JP To VN (2026-08-06)

- **Trạng thái**: ✅ 7/7 tests pass (20.4s, ASR whisper-small thật trên MPS) · 1 bug nghiêm trọng **đã xác nhận bằng đo thực tế** · 4 bug P1 xác nhận bằng đọc code · ~8 mục P2/docs.
- **Đối tượng**: `local-bridge/` (main, endpoints, core, schemas, services, utils, tests) + `web/index.html` + plan/wiki/README/walkthrough. Đã re-read toàn bộ từ disk (AGENTS §2).

---

## 1. Xác nhận bằng thực tế (2026-08-06)

| Hạng mục | Kết quả |
|---|---|
| `python3 -m unittest discover -s tests` | ✅ Ran 7 tests in **20.415s** — OK (test ASR chạy whisper-small thật trên sine wave, chiếm ~18s) |
| WS + audio → ASR thật | ✅ pipeline chạy, `is_final` contract hoạt động (đã verify trước đó; E2E trong wiki) |
| **Event-loop blocking** (đo mới) | ❌ **GET /health trong lúc WS đang xử lý audio → mất 23.6s** — server treo toàn bộ mọi request khác suốt thời gian ASR + model load |

---

## 2. Bug P0/P1 (cần fix)

### 2.1 [CONFIRMED bằng đo] WS handler blocking chặn cả event loop — `endpoints.py:57-143`
- `websocket_translate` là `async def` nhưng gọi **đồng bộ** `asr_service.transcribe()` (~6s/window, lần đầu +~12s load model) và `translation_service.translate()` ngay trong handler.
- Đo thực tế: gửi 1 chunk audio 2s qua WS, request `/health` phát ra ngay sau đó **mất 23.6s** mới trả lời. Mọi client khác (WS thứ 2, REST, health check) đều bị treo theo — với nhiều client sẽ chồng chất.
- Fix tối giản: đổi handler sang sync `def` (FastAPI tự chạy trong threadpool) hoặc bọc `await asyncio.to_thread(...)` quanh transcribe/translate. `/api/translate` cũng blocking nhưng mức độ ít hơn.

### 2.2 [CONFIRMED đọc code] Partial cards cũ không bị dọn khi finalize — `web/index.html:477-482`
- Server gửi 1 partial mỗi window (sliding step 1.5s) → utterance 4s tạo 2 partial, cả hai đều **append** card.
- Khi final đến: UI chỉ xóa **card cuối** rồi append final → partial trước đó (text giữa câu, có thể hallucinate như `コンニング`) nằm lại vĩnh viễn trong transcript. Bug "dedupe" hiện tại chỉ đúng cho trường hợp đúng 1 partial.
- Fix gợi ý (MVP): theo dõi các card partial kể từ final gần nhất và thay **toàn bộ** nhóm đó bằng card final; hoặc gom theo `utterance_id` do server cấp; hoặc UI chỉ giữ 1 card "partial đang hiện" được update tại chỗ.

### 2.3 [CONFIRMED đọc code] Mic bị xuất ra loa — feedback loop — `web/index.html:553-554`
- `scriptProcessor.connect(audioContext.destination)` phát lại tiếng micro qua loa → hú/echo khi dùng loa ngoài.
- Fix: connect vào `GainNode` với `gain=0` (hoặc bỏ connect nếu `onaudioprocess` vẫn fire — gain-0 là an toàn nhất).

### 2.4 [PLAUSIBLE] Sample rate không được truyền qua — server giả định 16kHz cố định
- UI khai `AudioContext({sampleRate: 16000})` nhưng nhiều browser/device chạy 44.1k/48k; nếu bị ignore → PCM gửi lên không phải 16kHz → ASR nghe sai pitch/tốc độ.
- `AudioChunkMessage.sample_rate` đã có field nhưng server **không đọc** (endpoints.py dùng `config.sample_rate`).
- Fix: gửi `sample_rate: audioContext.sampleRate` trong từng chunk, server resample về 16k (numpy) hoặc ít nhất log cảnh báo khi khác config.

### 2.5 [CONFIRMED đọc code + errors.log] ASR retry `load_model` mỗi window khi fail + fallback mock âm thầm
- Khi load model fail (`is_loaded=False, pipe=None`), mỗi window `transcribe()` gọi lại `load_model()` → retry tốn kém + spam log (bằng chứng: 3 dòng WARNING trùng lặp trong `errors.log` từ lỗi scipy cũ).
- Fallback mock trả text giả `こんにちは、リアルタイム翻訳テストです。` cho **mọi** audio không im lặng; UI không hiển thị engine state → user không phân biệt được dịch thật/giả.
- Fix: flag `load_failed` (retry 1 lần thôi), và UI gọi `/api/status` (hoặc WS hello) để hiển thị badge engine ASR/MT/fallback.

---

## 3. Bug P2 (nhỏ — dọn cùng đợt)

| # | Mục | Vị trí |
|---|---|---|
| 3.1 | Dead code: `filter_silence()` không ai gọi; `AudioChunkMessage` schema không dùng; config `chunk_duration_sec`, `min_speech_duration_sec`; `AudioBufferManager.silence_count` | vad_service.py:26-46, schemas/translation.py:20-24, config.py:13,15, audio_buffer.py:12,70 |
| 3.2 | `confidence` hardcode giả (ASR 0.95, REST 1.0) | asr_service.py:53, endpoints.py:50 |
| 3.3 | `itemCounter` đếm cả partial → "N câu" sai nghĩa | index.html:469-470 |
| 3.4 | CORS `allow_origins=["*"]` + `allow_credentials=True` (combo vô hiệu, Starlette bỏ credentials) + bind `0.0.0.0` → bridge hở cho mọi trang web/LAN dùng dịch vụ | main.py:19-25, config.py:7 |
| 3.5 | Dict fast-path chỉ exact-match cả chuỗi — `こんにちは。` (có dấu câu) miss dict | translation_service.py:67 |
| 3.6 | `load_model()` MT race check-then-act khi nhiều connection cùng lúc | translation_service.py:71-72 |
| 3.7 | WS `receive_text()`: client gửi binary → exception → đóng session (chấp nhận được, chỉ note) | endpoints.py:66 |

## 4. Docs / spec debt

| # | Mục | Vị trí |
|---|---|---|
| 4.1 | README nói `walkthrough.md (đang skeleton)` — thực tế walkthrough đã đầy đủ | README.md:72 |
| 4.2 | 3/5 skill thiếu SKILL.md: `skills/local-bridge`, `skills/realtime-translate`, `skills/realtime-regression` là **thư mục trống** dù AGENTS §5 khai đủ 5 skill | skills/ |
| 4.3 | `testdata/` trống — không có golden audio (konnichiwa.wav dùng lúc verify đã biến mất) → không có regression test với fixture thật | testdata/ |
| 4.4 | `test_asr_service` chạy whisper thật trên sine wave (~18s của 20.4s) — chậm, mong manh; unit test nên mock, giữ 1 integration test riêng có fixture | tests/test_pipeline.py:66-71 |

## 5. Không phải bug (ghi nhận)

- `is_final` contract (server finalize + UI dedupe) — đúng cho case 1 partial, hoạt động như thiết kế.
- Sliding window overlap 1.5s (audio trùng giữa các window) — thiết kế chủ ý.
- scipy pin `==1.14.1` — đúng, đã cứu ASR khỏi fallback âm thầm.
- Plan cũ Phase 1-3 đã khớp reality (đã cập nhật 08-06).

## 6. Kết luận

MVP vẫn đứng vững (7/7 pass, E2E chạy thật). **Bug chặn nhất là §2.1** (server treo 20s+ cho mọi client khác khi có 1 luồng ASR — phá vỡ giả định "realtime" khi >1 client hoặc cần health check), kế đến là §2.2 (transcript nhiễu partial cũ). Cả hai đều fix nhỏ. Đề xuất: plan mới = đợt fix P1 (Phase A) → gap nhỏ + docs (Phase B) → Phase 4 latency (whisper.cpp/MLX) như plan cũ đã ghi.
