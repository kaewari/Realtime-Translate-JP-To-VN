---
name: local-bridge
description: >
  Start, check health, and debug the local-bridge backend (FastAPI + WebSocket,
  port 8765). Covers run commands, endpoints, common failure signatures
  (scipy pin, lazy-load models, load_failed fallback, resample warning), and
  the errors.log append rule. Use for any task that starts the bridge, hits
  its HTTP/WS endpoints, or investigates a bridge runtime error.
---

# Local Bridge

## Run

```bash
cd local-bridge
uvicorn app.main:app --port 8765          # dev; or `source .venv/bin/activate` first
```

## Endpoints

| Endpoint | Use |
|---|---|
| `GET /health` | liveness — must stay fast (<ms) even mid-transcribe |
| `GET /api/status` | `asr_engine`, `mt_engine`, `sample_rate`, `uptime_seconds` |
| `POST /api/translate` | `{"text": "こんにちは"}` → `{"ja_text", "vi_text", ...}` |
| `WS /ws/translate` | realtime pipeline — see `realtime-translate` skill |
| `GET /docs` | OpenAPI |

## Layout

`app/main.py` (entry, CORS, mounts `web/`) · `app/api/endpoints.py` (HTTP + WS routes) ·
`app/services/` (asr, translation, vad, audio_buffer) · `app/core/config.py` ·
`app/schemas/translation.py` · `app/utils/logger.py`.

## Known failure signatures

- **ASR silently falls back to mock**: `asr_engine` shows `fallback-asr (load failed)`.
  Check `scipy==1.14.1` is pinned — `scipy>=1.15` wheels fail dyld on macOS 27/Python 3.10
  (`__thread_bss` in `_spropack`) → transformers pipeline crashes → fallback.
  Also check model weights cached (`~/.cache/huggingface/hub/`); first load ~10-30s.
- **MT shows `[Dịch: …]` / `mt_engine=FallbackDict`**: MarianTokenizer needs `sentencepiece`
  (`sentencepiece>=0.2.0` in requirements). Missing → load fails → dict-only fallback wraps
  unknown phrases as `[Dịch: JA]`. Restart bridge after install (`load_failed` is sticky).
- **Load failure is sticky**: `load_failed=True` disables retry per window (was spamming
  errors.log). Restart the bridge after fixing the cause.
- **Blocking inference on event loop**: ASR/MT must go through `asyncio.to_thread`.
  Regression: `curl /health` during a WS transcribe must not stall.
- **CORS**: `allow_origins=["*"]` with `allow_credentials` is a no-op combo — credentials
  are intentionally omitted (main.py).
- **client sample_rate != 16000**: server resamples via numpy interp and logs the warning
  once per WS session — one line per session is correct, repeated lines are a bug.
- **Flush with no new audio**: server resends the last partial with `is_final=true` so
  clients always get a final marker.

## Errors

Every error observed (build, runtime, test, user report) appends one line to
`local-bridge/errors.log` in bridge format — `ERROR:bridge:<what failed + where>` or
`WARNING:bridge:<...>`, one line per distinct error, no timestamps (AGENTS §6).
Logging never replaces the fix.
