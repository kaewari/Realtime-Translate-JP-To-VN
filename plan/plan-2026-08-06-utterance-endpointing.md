<!-- date: 2026-08-06 -->
<!-- source: chat:utterance-jump · user: lưu plan + đưa DeepSeek làm -->
<!-- cursor: .cursor/plans/fix_utterance_jump_d62d24ae.plan.md -->

# Plan: Utterance endpointing — câu chưa hết đã nhảy timeline

> Bug: đang nói / chưa đọc hết câu trên UI đã nhảy sang kết quả ASR khác; tỉ lệ lỗi cao dù nói rõ.  
> Root cause: sliding window greedy 0.5–3s trong `AudioBufferManager.get_window` cắt giữa câu.

## Executor

| | |
|--|--|
| **Agent** | **free-claude-code / DeepSeek V4 Flash** → branch agent `deepseek/dev` |
| **Task branch** | `utterance-end/dev` (AGENTS §1a) |
| **Verify sau** | Cursor / Bugbot |
| Không dùng | Antigravity Flash cho task này (đã có plan locked) |

Thứ tự gate: implement trên `utterance-end/dev` → commit + push task branch → plan đóng → merge vào `deepseek/dev` → xóa `utterance-end/dev` → Cursor verify.

## Nguyên tắc (ponytail)

- Fix root cause buffer, không vá UI.
- Không thêm dependency; tái dùng energy VAD hiện có.
- Không gửi partial giữa câu (YAGNI preview).
- 1 runnable unit check cho logic emit.

---

## Root cause

[`local-bridge/app/services/audio_buffer.py`](../local-bridge/app/services/audio_buffer.py) `get_window`: mỗi chunk khi ≥0.5s + speech → cắt ≤3s; buffer ≤3s **xóa hết**; >3s nhảy step 1.5s → ASR mid-utterance → UI nhảy “timeline”.

## Fix (locked) — silence endpointing

**Gom khi nói; ASR chỉ khi im lặng / max / stop mic.**

Config ([`config.py`](../local-bridge/app/core/config.py)):

| Param | Giá trị |
|-------|---------|
| `endpoint_silence_sec` | `0.6` |
| `max_utterance_sec` | `8.0` |
| `min_speech_sec` | `0.4` |

`pop_utterance()` trong `audio_buffer.py`:

1. Append PCM (giữ resample).
2. Trailing silence: VAD trên tail ~100–200ms.
3. Emit khi: silence ≥ 0.6s sau speech ≥ 0.4s, **hoặc** buffer ≥ 8s, **hoặc** `flush()` (`is_final`).
4. Silence-end: cắt speech, overlap 0. Max-cap force: overlap 0.2s cuối tùy chọn (ponytail ok).

[`endpoints.py`](../local-bridge/app/api/endpoints.py): chunk thường → `pop_utterance()`; `is_final` → `flush()`. Bỏ gọi `get_window` trên stream (đổi tên / giữ wrapper gọi `pop_utterance` nếu test cũ còn).

## Checklist

- [x] config 3 field
- [x] `pop_utterance` + tests (speech+silence → 1 emit; continuous &lt; max → 0; ≥ max → 1)
- [x] wire WS endpoints
- [x] suite xanh
- [x] tick plan + wiki; commit `utterance-end/dev`; push; merge `deepseek/dev`; xóa task branch

## Mốc

- [x] Plan đóng — ngày: 2026-08-06 · verified Cursor: 2026-08-06 (disk: `pop_utterance` + config 3 field + WS wire; `get_window` gone; 11/11 unittest OK; SHA `3393934` trên `deepseek/dev`)

## Out of scope

TTS; đổi model ASR; streaming partial preview liên tục.

---

## Appendix — Handoff prompt (DeepSeek / free-claude-code)

```text
Bạn là lazy senior (ponytail). Fix bug utterance jump cho Realtime Translate JP To VN.

BUG: câu chưa hết đã nhảy timeline / ASR lỗi cao dù nói rõ.
ROOT: local-bridge/app/services/audio_buffer.py get_window — greedy cắt 0.5–3s giữa câu, xóa buffer.

BẮT BUỘC:
1. Đọc AGENTS.md (§0 ponytail, §1a branches, §2 disk wins, §6 errors.log).
2. Living plan: plan/plan-2026-08-06-utterance-endpointing.md — làm đúng fix locked.
3. Branch: checkout/create utterance-end/dev TRƯỚC khi sửa. Agent name deepseek (free-claude-code backend).
4. Không thêm dependency. Không partial giữa câu. Không đụng Phase C engine.

FIX:
- config.py: endpoint_silence_sec=0.6, max_utterance_sec=8.0, min_speech_sec=0.4
- audio_buffer.py: pop_utterance() — emit chỉ khi silence≥0.6s sau speech≥0.4s, hoặc ≥8s, hoặc flush(). Reuse vad_service energy trên tail.
- endpoints.py WS: pop_utterance thay get_window; is_final vẫn flush().
- tests: speech 2s + silence 0.7s → 1 emit ~2s; continuous <8s → 0 emit; ≥8s → 1 emit. Full unittest xanh.

SAU KHI XONG:
1. Tick checklist + mốc trong living plan; wiki/topics/realtime-translate.md + wiki/log.md ngắn.
2. Commit + push origin utterance-end/dev.
3. Merge vào deepseek/dev, push deepseek/dev, xóa utterance-end/dev (local+remote).
4. Không push master (chưa phải plan tổng mới).
5. Trả về: file đổi, test result, SHA branch.

Không tự verified — user chạy Cursor/Bugbot.
```
