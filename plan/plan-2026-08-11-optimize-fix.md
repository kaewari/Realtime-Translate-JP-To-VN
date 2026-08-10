<!-- date: 2026-08-11 -->
<!-- source: chat:optimize-fix · user: đọc sourcecode, viết plan optimize/fix, code, test -->

# Plan: Optimize & Fix — Realtime Translate JP To VN

> Baseline: review 2026-08-07 (100% plans closed) · master `de61b62`+ · mlx-whisper ~65ms (cached) · 12/12 tests pass

## Phân tích thực tế (disk reads 2026-08-11)

| Vấn đề | File | Mức độ | Mô tả |
|--------|------|--------|-------|
| **WS reconnect backoff cứng 3s** | `web/index.html:671` | P1 | `setTimeout(connectWS, 3000)` — không exponential, tốn CPU khi server down lâu |
| **AudioContext tạo mới mỗi lần** | `web/index.html:874` + `952` | P1 | `new AudioContext()` mỗi `startRecording`, `close()` mỗi `stopRecording` — Safari/iOS leak, latency khởi tạo |
| **Latency đo sai** | `local-bridge/app/api/endpoints.py:115` | P2 | `latency = time.time() - start_t` tính từ lúc *nhận* WS msg, không phải ASR+MT inference time |
| **localStorage XSS** | `web/index.html:710-718` | P2 | Lưu `innerHTML` thô → restore KHÔNG sanitize, vector XSS nếu attacker inject card HTML |
| **mlx_whisper params mặc định** | `local-bridge/app/services/asr_service.py:74` | P2 | Thiếu `temperature=0.0` (greedy) + `no_speech_threshold=0.6` → hallucination trên noise |
| **Translation cache missing** | `local-bridge/app/services/translation_service.py:62` | P2 | Không `@lru_cache` cho `translate` — câu trùng lặp (nhé) vẫn chạy full inference |
| **WHISPER_JUNK chưa đủ** | `local-bridge/app/services/asr_service.py:8` | P3 | Thiếu các outro phổ biến: "チャンネル登録", "高評価", "共有", "コメント" |

---

## Phase A — P1 Fixes (Fast, high impact)

### A1. WebSocket exponential backoff + jitter
**File**: `web/index.html` (function `connectWS`)
- Thêm state `reconnectAttempts = 0`, max 10 attempts
- Delay: `Math.min(1000 * 2^attempts + random(0, 1000), 30000)`
- Reset `reconnectAttempts = 0` khi `ws.onopen`

### A2. AudioContext suspend/resume thay vì tạo mới
**File**: `web/index.html`
- Global `audioContext` giữ nguyên giữa các session
- `startRecording`: nếu chưa có thì `new`, rồi `audioContext.resume()`
- `stopRecording`: `scriptProcessor.disconnect()`, `audioContext.suspend()` (KHÔNG `close()`)
- Chỉ `close()` khi page unload (`beforeunload`)

---

## Phase B — P2 Fixes (Correctness)

### B1. Latency đo đúng ASR+MT inference time
**File**: `local-bridge/app/api/endpoints.py`
- Đổi: `asr_start = time.time()` trước `await asyncio.to_thread(asr_service.transcribe...)`
- Sau ASR xong: `asr_latency = time.time() - asr_start`
- Sau MT xong: `total_latency = time.time() - asr_start`
- Response: `latency_ms = round(total_latency, 2)` (ASR+MT), thêm `asr_latency_ms` optional vào schema

### B2. Sanitize localStorage restore
**File**: `web/index.html` (`restoreSession`)
- Thay `jaList.innerHTML = jaHTML` bằng parse HTML an toàn:
  - `DOMParser().parseFromString(jaHTML, 'text/html').body.innerHTML` rồi validate chỉ cho phép `.transcript-card` + `.card-text` + `.copy-btn`
  - Hoặc đơn giản: chỉ restore text content, rebuild card qua `addTranslationResult` (nhưng mất timestamp/latency)
- Compromise: whitelist sanitizer nhỏ gọn (`DOMPurify` quá to → tự viết `escapeHtml` + rebuild)

### B3. mlx_whisper decode params
**File**: `local-bridge/app/services/asr_service.py`
- Thêm vào call `transcribe`:
  ```python
  res = self.pipe.transcribe(
      audio_data, path_or_hf_repo=self.model_path,
      language=config.asr_language, task="transcribe",
      temperature=0.0, no_speech_threshold=0.6
  )
  ```
- `condition_on_previous_text=False` (giúp giảm hallucination khi streaming)

### B4. `@lru_cache` cho TranslationService.translate
**File**: `local-bridge/app/services/translation_service.py`
- Import `functools.lru_cache`
- `@lru_cache(maxsize=512)` trên `translate` (key = `text.strip()`)
- Note: fallback dict path không cache (đã O(1))

---

## Phase C — P3 Polish

### C1. Mở rộng WHISPER_JUNK
**File**: `local-bridge/app/services/asr_service.py`
- Thêm set: `{"チャンネル登録", "高評価", "共有", "コメント", "登録", "いいね", "通知", "概要欄"}`
- Dùng `frozenset` + compact check như cũ

---

## Test Strategy

| Phase | Commands |
|-------|----------|
| Pre-fix baseline | `cd local-bridge && python -m unittest tests.test_pipeline -v` |
| Post-fix verify | Same + manual: serve UI, toggle mic 10x, kill/restart server, check reconnect |
| Benchmark ASR | `cd local-bridge && python benchmark_asr.py` (expect stable <100ms avg) |
| XSS test | DevTools Console: `localStorage.setItem('rt_ja', '<img src=x onerror=alert(1)>')` reload → no alert |

---

## Mốc hoàn thành

- [x] Phase A (A1, A2) — WS reconnect exponential backoff & AudioContext reuse done (tested 12/12)
- [x] Phase B (B1, B2, B3, B4) — Latency tracking split, localStorage sanitization, mlx_whisper params, translation caching done (tested 12/12)  
- [x] Phase C (C1) — Extended WHISPER_JUNK outliers done
- [x] Plan closed & wiki log updated