---
name: realtime-regression
description: >
  Regression procedure for the JP→VN realtime pipeline: run the unittest suite,
  verify ASR/MT/VAD/buffer/WS behavior, check engines via /api/status, watch
  latency (event loop must not block), and audit errors.log for duplicates.
  Use after any change touching capture, ASR, translation, buffering, or WS.
---

# Realtime Regression

## 1. Suite

```bash
cd local-bridge && source .venv/bin/activate
python3 -m unittest tests.test_pipeline -v
```

8 tests: health, status, REST translate (こんにちは → Xin chào), VAD
(sine vs zeros), buffer, ASR unit (mocked pipe — fast), ASR integration
(real mlx-whisper on golden wav), WS text flow (ありがとう → Cảm ơn).

## 2. Golden fixture

`testdata/audio/konnichiwa-16k.wav` — gitignored, regenerable:

```bash
say -v Kyoko -r 160 "こんにちは" -o /tmp/k.aiff
ffmpeg -y -i /tmp/k.aiff -ar 16000 -ac 1 -c:a pcm_s16le testdata/audio/konnichiwa-16k.wav
```

The integration test skips with a regen hint if the file is missing (e.g.
fresh clone). Missing fixture ≠ broken pipeline.

## 3. Engine check

`curl localhost:8765/api/status` → `asr_engine` must be `mlx-whisper-small-mlx`
(or the configured model), `mt_engine` `MarianMT`. `fallback-asr (load failed)`
means the ASR is mocked — fix the root cause (scipy pin, weights), don't accept
the fallback as "passing" (see `local-bridge` skill).

## 4. Latency / event-loop

- `curl localhost:8765/health` during a WS transcribe must stay <~10ms.
  Regression of the P0 (was 23.6s): ASR/MT must run in `asyncio.to_thread`.
- WS responses report `latency_ms`; steady-state ASR ~63ms/window after warmup.
- First WS call can take ~20s (model weight cache) — not a regression.

## 5. errors.log audit

After the run, `local-bridge/errors.log` must not have duplicated per-window
WARNING lines (load retry spam was removed; resample warning is once per
session). New lines for real failures only, in `ERROR:bridge:`/`WARNING:bridge:`
format (AGENTS §6).
