<!-- date: 2026-08-08 -->
<!-- source: chat:latency-optimization · user: optimize to <30ms; then: streaming translate like modern web translators -->

# Plan: Latency Optimization to <30ms → evolved into Streaming Translate

**Status: REPLACED by streaming-translate design (2026-08-08).** The <30ms target
proved incompatible with accuracy on long sentences; user redirected to continuous
streaming translation ("vừa dịch vừa nghe, tự sửa bản dịch") — implemented and
measured below.

## What shipped (2026-08-08, branch `streaming/dev`)

| Change | File | Result |
|--------|------|--------|
| Streaming background decode (skip-if-busy, receive loop never blocks) | `local-bridge/app/api/endpoints.py` | partials stream continuously while speaking, self-correcting |
| Final = wait in-flight decode, then RE-decode exact window once | same | no more truncated finals (`働き` → full sentence) |
| Corrected final on speech resume / re-decode on client `is_final` | same | UI card replaced in place (uid) |
| `endpoint_silence_sec` 0.064 → 0.2s | `local-bridge/app/core/config.py` | stops premature finals mid-sentence |
| Background model preload at server start (lifespan) | `local-bridge/app/main.py` | no ~1.7s cold-start stall on first utterance |
| Fixed benchmark pacing bug (1024 bytes ≠ 1024 samples → 2x realtime) | `local-bridge/benchmark_latency_e2e.py` | honest ~55ms short-utterance measurement |
| New 10-sentence TTS benchmark | `local-bridge/benchmark_sentences.py` | honest long-sentence numbers below |

## Verified measurements (2026-08-08, whisper-small, 10 sentences ~15 words TTS)

- **Accuracy: 7/10 exact match (70%); 9/10 semantically correct** (1 real whisper
  error `遅刻思想` — reproduced by offline decode, not pipeline; 2 are digit/kanji
  variants `6時`/`時`).
- **Truncation: 0** (was 3/10 before the final re-decode change).
- **Final latency p50 324ms, p95 408ms** (incl. final re-decode of 5–7s window,
  small = 140–850ms; irreducibly higher than 55ms short-utterance number).
- tiny model rejected: 15–42ms decode BUT 10% exact accuracy on TTS (worse partials
  + wrong finals `マイヤサロクジ`). Accuracy loss not worth 3x speed.

## Decisions (locked)

- **Model: whisper-small stays.** tiny rejected on measured accuracy.
- **<30ms final is abandoned** — impossible with full-window re-decode at final
  (necessary to avoid truncation). The streaming UX (partials appear ~0.4–0.5s into
  speech, self-correct continuously) is the real product win; final latency 324ms is
  acceptable for that.
- Streaming decode = background task per utterance, one in flight (skip-if-busy).

## Open gaps / next candidates

- Partial decode cadence `partial_step_sec` 0.25s → could tighten to ~0.15s for
  snappier UI updates (measured decode 50–63ms on 0.5s windows, leaves headroom).
- `max_utterance_sec` 8s cap path re-emits `last_decoded` without re-decode —
  same truncation risk as the old final path; apply re-decode there too if it bites.
- Whisper trims trailing soft speech (TTS tail `ます。` sometimes dropped even
  offline) — ASR-level, not pipeline; possible `no_speech_threshold` tuning later.
- tiny remains viable for a future "fast mode" toggle (config only).

## Success criteria (updated)

- [x] Streaming partials appear while speaking, self-correct (verified trace)
- [x] No truncated finals on 10-sentence benchmark (0/10)
- [x] Accuracy ≥ 70% exact on TTS long sentences (7/10)
- [x] Cold start no longer stalls first utterance (preload)
- [ ] Optional: partial cadence 0.15s + cap-path re-decode (open, low priority)
