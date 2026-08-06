---
name: realtime-translate
description: >
  Domain knowledge for the realtime JP→VN pipeline: mic capture, VAD, window
  buffer, ASR (mlx-whisper), MT (MarianMT + dict), and the WS protocol
  contracts (is_final, sample_rate, data-partial-group). Read before touching
  capture, ASR, translation, audio buffering, or the WebSocket flow.
---

# Realtime Translate JP → VN

## Pipeline

```
mic → Web Audio (16 kHz mono) → PCM16 base64 over WS audio_chunk
    → server: RMS VAD → window buffer (3s) → ASR (mlx-whisper, ja)
    → MT (MarianMT opus-mt-ja-vi + dict fast-path) → WS TranslationResponse
```

## WS protocol (`/ws/translate`)

Client events (JSON): `audio_chunk` (`audio_base64`, `is_final`, `sample_rate`),
`text` (direct Japanese), `ping` (`pong` reply). Server responses are
`TranslationResponse` = `{id, ja_text, vi_text, is_final, confidence, latency_ms}`.

## Contracts (do not break)

- **`sample_rate`**: client sends its AudioContext rate (16k requested, may be
  44.1k/48k). Server resamples to 16k (numpy `np.interp`) and logs a warning
  once per session (`sr_warned`). Browser must request `{sampleRate:16000, channelCount:1}`.
- **`is_final`**: on flush the server delivers the last partial as final even if
  the flush had no new audio — clients must handle the final marker and dedupe
  (replace the group, don't append). UI removes `[data-partial-group="N"]` cards
  then appends one final card; `itemCounter` increments only on final.
- **`confidence`**: `Optional[float]` — real mlx output is `None`, fallback uses
  `0.0` for silence. Never hardcode fake confidences.
- **Dict fast-path**: lookup strips trailing `。、！？` before matching.
- **Partial groups**: each utterance (mic start / text send) bumps `partialGroup`;
  partials carry `data-partial-group` so finalize cleans exactly that group.
- **Mic feedback**: the script processor connects to a `GainNode` with `gain=0`
  (not the destination) — keeps onaudioprocess firing without playing mic audio.
- **Audio graph**: `source → scriptProcessor(4096) → muteGain(0) → destination`.

## Engines & latency

- ASR: `mlx_whisper.transcribe(audio, path_or_hf_repo=model, language="ja",
  task="transcribe")`; `openai/whisper-small` maps to `mlx-community/whisper-small-mlx`.
  Warmup transcribe of zeros at load. MPS ~63ms/window; first call ~20s (weight cache).
- MT: MarianMT Helsinki-NLP/opus-mt-ja-vi; dict fallback ~0.00s for known phrases.
- ASR/MT run via `asyncio.to_thread` — never block the event loop.

## Key files

`local-bridge/app/api/endpoints.py` (WS handler) · `app/services/asr_service.py` ·
`app/services/translation_service.py` · `app/services/audio_buffer.py` ·
`app/services/vad_service.py` (RMS energy, `energy_threshold`) ·
`web/index.html` (capture, partial-group UI, copy buttons).
