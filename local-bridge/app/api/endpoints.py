"""API router for local-bridge endpoints."""
import asyncio
import time
import uuid
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from app.core.config import config
from app.schemas.translation import (
    TextTranslationRequest,
    TranslationResponse,
    ServerStatusResponse
)
from app.services.asr_service import asr_service
from app.services.translation_service import translation_service
from app.services.audio_buffer import AudioBufferManager
from app.utils.logger import log_error, log_warning

router = APIRouter()
START_TIME = time.time()

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "local-bridge", "port": config.port}

@router.get("/api/status", response_model=ServerStatusResponse)
async def get_status():
    """Get system and engine status."""
    return ServerStatusResponse(
        status="online",
        asr_engine=asr_service.engine_name,
        mt_engine="MarianMT" if translation_service.is_loaded else "FallbackDict",
        sample_rate=config.sample_rate,
        uptime_seconds=round(time.time() - START_TIME, 2)
    )

@router.post("/api/translate", response_model=TranslationResponse)
async def translate_text(req: TextTranslationRequest):
    """REST endpoint for direct text translation."""
    start_t = time.time()
    try:
        vi_text = await asyncio.to_thread(translation_service.translate, req.text)
        latency = (time.time() - start_t) * 1000.0
        return TranslationResponse(
            id=str(uuid.uuid4())[:8],
            ja_text=req.text,
            vi_text=vi_text,
            is_final=True,
            confidence=None,
            latency_ms=round(latency, 2)
        )
    except Exception as e:
        log_error(f"API translate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/translate")
async def websocket_translate(websocket: WebSocket):
    """WebSocket endpoint for real-time streaming translation.

    Streaming design (latency target: final <=100ms after speech ends):
    - Every speech chunk with new content triggers a partial decode (is_final=false,
      cadence partial_step_sec) so results appear while the user is still speaking.
    - The FIRST silence chunk after speech triggers an OPTIMISTIC final
      (is_final=true) using the last decoded partial — no re-run of ASR/MT, so the
      response goes out within ~1 chunk of speech end.
    - If speech resumes within resume_grace_sec, a corrected partial+final with the
      SAME utterance_id is sent; the UI replaces the card instead of appending.
    - latency_ms = wall time since the last speech sample (no clock sync needed).
    """
    await websocket.accept()
    buffer_mgr = AudioBufferManager(sample_rate=config.sample_rate)
    sr_warned = False  # warn once per session when client sample_rate != config
    utterance_id = 0
    last_gen = 0
    last_speech_ts = None  # arrival time of the END of the last speech chunk
    last_decoded = None    # (ja, vi) of the latest partial decode
    last_decoded_ts = 0.0
    decode_task = None     # in-flight background streaming decode (None = idle)
    pending_final = False  # an optimistic final was sent for the current utterance

    def _build_response(ja_text, vi_text, is_final, latency_ms, confidence=None):
        return TranslationResponse(
            id=str(uuid.uuid4())[:8],
            ja_text=ja_text,
            vi_text=vi_text,
            is_final=is_final,
            confidence=confidence,
            latency_ms=round(latency_ms, 2),
            utterance_id=utterance_id,
        )

    async def _emit(ja_text, vi_text, is_final, confidence=None):
        latency = (time.time() - last_speech_ts) * 1000.0 if last_speech_ts else 0.0
        await websocket.send_json(_build_response(ja_text, vi_text, is_final, latency, confidence).model_dump())

    async def _transcribe_window():
        """ASR + translate the current buffer once (runs in a thread; loop stays free)."""
        window = buffer_mgr.partial_window()
        asr_res = await asyncio.to_thread(asr_service.transcribe, window, config.sample_rate)
        ja_text = asr_res.get("text", "").strip()
        if not ja_text:
            return None
        vi_text = await asyncio.to_thread(translation_service.translate, ja_text)
        return (ja_text, vi_text)

    async def _decode_worker():
        """Streaming partial decode: decode + translate + emit, without blocking
        the receive loop. Skip-if-busy: only one decode in flight at a time,
        so audio intake is never stalled (latest window always wins)."""
        nonlocal decode_task, last_decoded, last_decoded_ts
        try:
            last_decoded_ts = time.time()
            result = await _transcribe_window()
            if result and (last_decoded is None or result[0] != last_decoded[0]):
                last_decoded = result
                await _emit(*result, False)
        finally:
            decode_task = None

    try:
        while True:
            data_str = await websocket.receive_text()
            try:
                msg_dict = json.loads(data_str)
            except Exception:
                # Direct Japanese text message
                msg_dict = {"event": "text", "text": data_str}

            event_type = msg_dict.get("event", "audio_chunk")

            if event_type == "ping":
                await websocket.send_json({"event": "pong", "timestamp": time.time()})
                continue

            if event_type == "text" and "text" in msg_dict:
                ja_text = msg_dict["text"].strip()
                if ja_text:
                    utterance_id += 1
                    vi_text = await asyncio.to_thread(translation_service.translate, ja_text)
                    await _emit(ja_text, vi_text, True)
                continue

            if event_type == "audio_chunk":
                is_final_msg = msg_dict.get("is_final", False)
                audio_b64 = msg_dict.get("audio_base64")
                if audio_b64:
                    chunk_sr = msg_dict.get("sample_rate", config.sample_rate)
                    if chunk_sr != config.sample_rate and not sr_warned:
                        log_warning(f"client sample_rate {chunk_sr} != {config.sample_rate}, resampling to 16k")
                        sr_warned = True
                    chunk_ts = time.time()
                    was_speech = buffer_mgr.add_base64_pcm16(audio_b64, source_sample_rate=chunk_sr)

                    if was_speech:
                        last_speech_ts = chunk_ts + buffer_mgr.last_chunk_dur
                        resumed_after_final = pending_final
                        pending_final = False
                        gen = buffer_mgr.utterance_generation
                        if gen != last_gen:
                            # confirmed pause before this speech -> new utterance
                            utterance_id += 1
                            last_gen = gen
                            last_decoded = None
                            last_decoded_ts = 0.0
                        elif resumed_after_final:
                            # speech resumed inside the grace window: re-decode right away
                            last_decoded_ts = 0.0
                        # Streaming decode: kick off a background partial decode.
                        # Skip-if-busy: if one is already running, let it finish —
                        # the next cadence tick will decode a fresher window anyway.
                        if (buffer_mgr.total_speech_sec >= config.min_speech_sec
                                and time.time() - last_decoded_ts >= config.partial_step_sec
                                and decode_task is None):
                            decode_task = asyncio.create_task(_decode_worker())

                # Optimistic final: first silence chunk after speech. Wait for any
                # in-flight streaming decode, then RE-decode the exact final window
                # once so the final text is never truncated (tiny: ~40ms).
                if buffer_mgr.should_emit_final() and not pending_final:
                    pending_final = True
                    if decode_task is not None:
                        await decode_task
                    result = await _transcribe_window()
                    if result:
                        last_decoded = result
                        await _emit(*result, True)
                    elif last_decoded:
                        await _emit(*last_decoded, True)

                # Long continuous speech: cap the window, finalize and start fresh.
                if buffer_mgr.should_cap():
                    if decode_task is not None:
                        await decode_task
                    if last_decoded:
                        await _emit(*last_decoded, True)
                    buffer_mgr.reset()
                    utterance_id += 1
                    last_gen = buffer_mgr.utterance_generation
                    last_decoded = None
                    last_decoded_ts = 0.0
                    pending_final = False

                if is_final_msg:
                    # Client stopped: re-decode the exact window and finalize.
                    if decode_task is not None:
                        await decode_task
                    result = await _transcribe_window()
                    if result:
                        last_decoded = result
                        await _emit(*result, True)
                    elif last_decoded:
                        await _emit(*last_decoded, True)
                    buffer_mgr.reset()
                    utterance_id += 1
                    last_gen = buffer_mgr.utterance_generation
                    last_decoded = None
                    last_decoded_ts = 0.0
                    pending_final = False
                    last_speech_ts = None

    except WebSocketDisconnect:
        pass
    except Exception as e:
        log_error(f"WebSocket session error: {e}")
        try:
            await websocket.close()
        except Exception:
            pass
