<!-- date: 2026-08-06 -->
<!-- source: chat:bugcheck-realtime-translate · user: đọc sourcecode, check bug, check plan để viết review và lập plan mới -->

# Plan: Bugfix đợt 2026-08-06 + Phase 4 latency — Realtime Translate JP To VN

> **Thay thế** `plan/plan-2026-08-05-realtime-translate-jp-to-vn.md` (Phase 1-3 ✅ done — đóng). Kế thừa: scipy pin, `is_final` contract, MPS default.
> Căn cứ: `review/codebase-bugcheck-2026-08-06.md` — 7/7 tests pass, event-loop blocking **đã đo thực tế 23.6s /health** (§2.1), 4 bug P1 + ~8 mục P2/docs.

## Nguyên tắc (ponytail)
- Fix nhỏ nhất đúng root cause; không thêm dependency, không thêm abstraction.
- Mỗi fix có 1 runnable check (assert smoke / test unit). Test chạy full suite trước + sau mỗi phase.
- Plan là living document — khi reality đổi, update plan trong file này (AGENTS §1).

---

## Phase A — Bugfix quick wins (P0/P1, ~1 buổi)

### A1. Offload ASR/MT khỏi event loop — `app/api/endpoints.py`
- **Bug (§2.1, CONFIRMED đo):** `async def websocket_translate` gọi blocking `transcribe()`/`translate()` trên event loop → /health treo 23.6s khi có 1 luồng WS.
- **Fix:** bọc `await asyncio.to_thread(...)` quanh `asr_service.transcribe()` và `translation_service.translate()` (hoặc đổi handler sync `def`). Áp dụng cả `/api/translate` nếu cùng pattern.
- **Check:** test unit: trong lúc WS đang ASR (mock sleep), GET /health trả <1s.

### A2. Dọn partial cards khi finalize — `web/index.html`
- **Bug (§2.2):** chỉ xóa card cuối → utterance nhiều window để lại partial giữa câu.
- **Fix:** track các card partial từ final gần nhất (`data-partial-group`), khi final đến thay toàn bộ nhóm đó bằng 1 card final. (Không cần server change — `is_final` + text đã đủ.)
- **Check:** mock WS: 2 partial + 1 final → transcript chỉ còn 1 card cho utterance đó.

### A3. Kill feedback loop mic→loa — `web/index.html`
- **Bug (§2.3):** `scriptProcessor.connect(audioContext.destination)` phát mic ra loa.
- **Fix:** connect qua `GainNode` gain=0. Không tắt `onaudioprocess` (vẫn cần data).
- **Check:** mở mic, không nghe thấy echo; audio meter vẫn chạy.

### A4. Sample rate contract — `web/index.html` + `app/api/endpoints.py` + `app/schemas/translation.py`
- **Bug (§2.4):** `AudioChunkMessage.sample_rate` có field nhưng server bỏ qua; browser có thể chạy 44.1k/48k.
- **Fix (min):** client gửi `sample_rate: audioContext.sampleRate`; server khi khác `config.sample_rate` → log 1 lần `WARNING:bridge:` + resample về 16k bằng numpy (hoặc reject chunk kèm message). Không thêm dependency.
- **Check:** gửi chunk 48k → server log WARNING, pipeline vẫn trả kết quả.

### A5. ASR `load_failed` flag + engine badge — `app/services/asr_service.py` + `web/index.html`
- **Bug (§2.5):** retry `load_model` mỗi window khi fail (spam errors.log — 3 dòng WARNING trùng); fallback mock âm thầm không phân biệt được với ASR thật.
- **Fix:** `load_failed` flag → retry tối đa 1 lần. UI gọi `/api/status` (đã có endpoint) hiển thị badge engine: `ASR: whisper-small (mps) · MT: marianmt` hay `ASR: MOCK (load failed)`.
- **Check:** test mock: fail load 2 lần → chỉ log 1 WARNING; status endpoint trả `engine` state.

### A6. Dọn dead code + nhỏ nhặt — đa file
- Xóa: `vad_service.filter_silence` (không ai gọi), `AudioChunkMessage` (dùng `AudioChunk` thật), config `chunk_duration_sec`/`min_speech_duration_sec`, `AudioBufferManager.silence_count`.
- `confidence` hardcode (0.95/1.0) → trả `None` hoặc bỏ field (whisper có score thật qua `return_all_scores`, nhưng YAGNI — MVP bỏ là đủ).
- `itemCounter` đếm final thay vì mọi WS message (§3.3).
- Dict fast-path: strip dấu câu tiếng Nhật `。、！？` trước khi exact-match (§3.5).
- **Check:** full test suite vẫn 7/7 (hoặc ít hơn nếu test dead code bị bỏ).

---

## Phase B — Gap nhỏ + docs (1 buổi, song song được với A)

- **B1. Nút copy text** transcript JA + VI (gap từ Phase 3 review) — `web/index.html`, 1 nút copy per card + copy all.
- **B2. Golden audio** — `testdata/audio/konnichiwa-16k.wav` (sinh bằng ffmpeg từ giọng TTS hoặc thu thật; đã từng có rồi mất) + regression test với fixture thay vì sine wave.
- **B3. Tách test ASR chậm** — mock whisper trong unit test, giữ 1 integration test dùng fixture thật (§4.4).
- **B4. 3 skill còn trống** — viết `skills/local-bridge/SKILL.md`, `skills/realtime-translate/SKILL.md`, `skills/realtime-regression/SKILL.md` (AGENTS §5 khai 5 nhưng mới có 2).
- **B5. README stale** — sửa dòng "walkthrough (đang skeleton)" → đã đầy đủ (README.md:72).
- **B6. CORS note** — `allow_origins=["*"]` + credentials combo vô hiệu: bỏ `allow_credentials` hoặc để nguyên + ghi rõ ràng rủi ro bind 0.0.0.0 (local dev — chấp nhận, chỉ note §3.4).
- **Check:** mỗi mục đều demo được thủ công; test suite pass.

---

## Phase C — Phase 4 latency (🔜 future, plan cũ kế thừa)

- Mục tiêu: < 1-2s/window (hiện MPS whisper-small ~5.8s).
- Lộ trình: whisper.cpp (Metal) hoặc mlx-whisper → model nhỏ hơn (base/tiny) cho chunk ngắn → đo lại latency.
- Điều kiện gating: Phase A+B đã merge; bridge vẫn đứng (tests pass) sau khi đổi engine.
- **Không làm trong đợt này:** extension/, ipad-app/, iphone-app/, macos-bridge-app/ (TBD, chưa ai yêu cầu).

---

## Mốc hoàn thành

- [ ] Phase A: 5 bug P0/P1 fix + 7/7 tests pass
- [ ] Phase B: copy button + golden audio + 3 SKILL.md + README
- [ ] Plan đóng khi cả A+B land — mỗi phase ghi ngày vào đây

## Out of scope (ghi lại để không bị hỏi lại)

- M2M100/NLLB thay MarianMT — khi cần chất lượng dịch, chưa phải bây giờ.
- Docker/cloud deploy, multi-user auth — local-first giữ nguyên.
