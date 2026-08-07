"""Sentence-level benchmark: 10 long JP sentences (~15 words each) via TTS + WS.

Generates audio with macOS `say` (Kyoko), streams each through the real WS
endpoint, measures speech-end -> final latency, and checks the final text
against the source sentence (normalized).

Usage: python benchmark_sentences.py [host:port] [--model small|tiny]
"""
import asyncio
import base64
import json
import os
import re
import statistics
import subprocess
import sys
import time
import wave

import websockets

SENTENCES = [
    "昨日の夜、友達と一緒に美味しいラーメンを食べに行きました。",
    "来週の月曜日に、私は東京の本社で新しいプロジェクトの会議があります。",
    "天気が良かったので、家族と一緒に公園を散歩してから映画を見ました。",
    "この本を読んでから、日本語の勉強をもっと頑張らなければならないと思いました。",
    "電車が遅れたので、会社に遅刻しそうになりましたが、なんとか間に合いました。",
    "新しいパソコンを買いたいですが、今月はお金があまり残っていません。",
    "毎朝六時に起きて、ジョギングをしてからシャワーを浴びます。",
    "京都に旅行に行ったとき、古いお寺をたくさん見て感動しました。",
    "彼女は大学で経済学を勉強していますが、卒業したら銀行で働きたいです。",
    "週末にスーパーで買い物をして、家でゆっくり料理をして過ごしました。",
]

WAV_DIR = "/tmp/bench_sentences"
CHUNK = 2048  # bytes = 1024 samples = 64ms @16k
SLEEP = CHUNK / 32000
NORM = re.compile(r"[\s、。！？「」・…]")


def norm(s: str) -> str:
    return NORM.sub("", s)


def make_wavs():
    os.makedirs(WAV_DIR, exist_ok=True)
    for i, s in enumerate(SENTENCES):
        wav = f"{WAV_DIR}/s{i}.wav"
        if not os.path.exists(wav):
            aiff = f"{WAV_DIR}/s{i}.aiff"
            subprocess.run(["say", "-v", "Kyoko", "-o", aiff, s], check=True)
            subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@16000", "-c", "1", aiff, wav], check=True)
            os.remove(aiff)
    return [f"{WAV_DIR}/s{i}.wav" for i in range(len(SENTENCES))]


async def one_sentence(ws, wav_path, silence_sec=0.5):
    """Stream one sentence, then keep streaming silence (like a live mic) for
    silence_sec so the server accumulates trailing silence -> confirmed pause.
    Reads responses concurrently so latencies are true arrival times."""
    with wave.open(wav_path, "rb") as w:
        pcm = w.readframes(w.getnframes())

    msgs = []

    async def reader():
        while True:
            try:
                msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
            except asyncio.TimeoutError:
                return
            if msg.get("ja_text"):
                msgs.append((time.time(), msg))

    rt = asyncio.create_task(reader())
    speech_end_sent = None
    for i in range(0, len(pcm), CHUNK):
        part = pcm[i:i + CHUNK]
        await ws.send(json.dumps({
            "event": "audio_chunk",
            "audio_base64": base64.b64encode(part).decode(),
            "is_final": False,
            "sample_rate": 16000,
        }))
        speech_end_sent = time.time() + len(part) / 32000
        await asyncio.sleep(SLEEP)
    silence = bytes(CHUNK)
    t_pause_end = time.time() + silence_sec
    while time.time() < t_pause_end:
        await ws.send(json.dumps({
            "event": "audio_chunk",
            "audio_base64": base64.b64encode(silence).decode(),
            "is_final": False,
            "sample_rate": 16000,
        }))
        await asyncio.sleep(SLEEP)
    await asyncio.sleep(0.8)
    rt.cancel()
    finals = [(t, m) for t, m in msgs if m.get("is_final")]
    if finals:
        t, m = finals[-1]
        return (t - speech_end_sent) * 1000, m.get("ja_text", ""), msgs
    return None, None, msgs


async def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1:8766"
    wavs = make_wavs()
    print(f"sentences: {len(SENTENCES)} | {host} | chunk 64ms | pause 0.5s silence-streamed")
    lats, matches = [], []
    async with websockets.connect(f"ws://{host}/ws/translate") as ws:
        for i, wav in enumerate(wavs):
            lat, text, msgs = await one_sentence(ws, wav)
            ok = text is not None and norm(text) == norm(SENTENCES[i])
            status = "OK " if ok else "MISMATCH" if text else "TIMEOUT"
            lat = lat or 0
            lats.append(lat)
            matches.append(ok)
            print(f"s{i+1:2d} [{status}] final={lat:6.1f}ms  got={text or '<none>'!r}")
    s = sorted(lats)
    p50 = statistics.median(s)
    p95 = s[min(len(s) - 1, int(0.95 * len(s)))]
    acc = sum(matches) / len(matches) * 100
    print(f"\nfinal latency: p50={p50:.1f}ms  p95={p95:.1f}ms  max={s[-1]:.1f}ms")
    print(f"accuracy (exact match): {acc:.0f}% ({sum(matches)}/{len(matches)})")


if __name__ == "__main__":
    asyncio.run(main())
