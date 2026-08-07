"""E2E latency benchmark: speech-end -> final response over a real WebSocket.

Sends the golden wav in realtime-pace chunks (2048 bytes = 1024 samples @16k =
64ms), then one 64ms silence chunk, and measures (final-received -
last-speech-chunk-sent) in ms. Reports p50/p95/min/max over N runs, plus
first-partial latency.
"""
import asyncio
import base64
import json
import statistics
import sys
import time
import wave

import websockets

WAV = "../testdata/audio/konnichiwa-16k.wav"
CHUNK = 2048  # bytes = 1024 samples = 64ms @16k
SLEEP = CHUNK / 32000  # 64ms realtime pacing
N = int(sys.argv[1]) if len(sys.argv) > 1 else 5


def load_pcm():
    with wave.open(WAV, "rb") as w:
        assert w.getframerate() == 16000 and w.getnchannels() == 1
        return w.readframes(w.getnframes())


async def one_run(ws, pcm):
    finals, partials = [], []
    n = len(pcm)
    speech_end_sent = None
    first_chunk_sent = None
    for i in range(0, n, CHUNK):
        part = pcm[i:i + CHUNK]
        if speech_end_sent is None:
            first_chunk_sent = time.time()
        await ws.send(json.dumps({
            "event": "audio_chunk",
            "audio_base64": base64.b64encode(part).decode(),
            "is_final": False,
            "sample_rate": 16000,
        }))
        speech_end_sent = time.time() + len(part) / 32000
        await asyncio.sleep(SLEEP)
    await ws.send(json.dumps({
        "event": "audio_chunk",
        "audio_base64": base64.b64encode(bytes(CHUNK)).decode(),  # 1 x 64ms silence chunk
        "is_final": False,
        "sample_rate": 16000,
    }))
    deadline = time.time() + 30
    while time.time() < deadline:
        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
        if not msg.get("ja_text"):
            continue
        lat = (time.time() - speech_end_sent) * 1000
        if msg.get("is_final"):
            finals.append(lat)
            break
        partials.append((time.time() - first_chunk_sent) * 1000)
    return finals, partials


async def main():
    pcm = load_pcm()
    print(f"wav: {len(pcm)} bytes = {len(pcm)/32000:.2f}s speech; chunk 2048B = 64ms; runs={N}")
    all_finals, first_partials = [], []
    for run in range(N):
        async with websockets.connect("ws://127.0.0.1:8766/ws/translate") as ws:
            finals, partials = await one_run(ws, pcm)
        if not finals:
            print(f"run {run+1}: NO FINAL within timeout")
            continue
        all_finals.append(finals[0])
        if partials:
            first_partials.append(partials[0])
        print(f"run {run+1}: final={finals[0]:7.1f}ms"
              + (f"  first_partial={partials[0]:7.1f}ms" if partials else "  no partials"))
    if all_finals:
        s = sorted(all_finals)
        p50 = statistics.median(s)
        p95 = s[min(len(s) - 1, int(0.95 * len(s)))]
        print(f"\nfinal speech-end->response: p50={p50:.1f}ms  p95={p95:.1f}ms  "
              f"min={s[0]:.1f}ms  max={s[-1]:.1f}ms")
    if first_partials:
        print(f"first partial (speech-start->partial): p50={statistics.median(first_partials):.1f}ms")


if __name__ == "__main__":
    asyncio.run(main())
