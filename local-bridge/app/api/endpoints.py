"""API router for local-bridge endpoints."""
import time
import uuid
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from app.core.config import config
from app.schemas.translation import (
    TextTranslationRequest,
    TranslationResponse,
    ServerStatusResponse,
    AudioChunkMessage
)
from app.services.vad_service import vad_service
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
        vi_text = translation_service.translate(req.text)
        latency = (time.time() - start_t) * 1000.0
        return TranslationResponse(
            id=str(uuid.uuid4())[:8],
            ja_text=req.text,
            vi_text=vi_text,
            is_final=True,
            confidence=1.0,
            latency_ms=round(latency, 2)
        )
    except Exception as e:
        log_error(f"API translate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/translate")
async def websocket_translate(websocket: WebSocket):
    """WebSocket endpoint for real-time streaming translation."""
    await websocket.accept()
    buffer_mgr = AudioBufferManager(sample_rate=config.sample_rate)
    last_result = None  # (ja, vi, confidence, latency) of last partial, for finalize
    
    try:
        while True:
            data_str = await websocket.receive_text()
            start_t = time.time()
            
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
                    vi_text = translation_service.translate(ja_text)
                    latency = (time.time() - start_t) * 1000.0
                    resp = TranslationResponse(
                        id=str(uuid.uuid4())[:8],
                        ja_text=ja_text,
                        vi_text=vi_text,
                        is_final=True,
                        confidence=1.0,
                        latency_ms=round(latency, 2)
                    )
                    await websocket.send_json(resp.model_dump())
                continue
                
            if event_type == "audio_chunk":
                audio_b64 = msg_dict.get("audio_base64")
                if audio_b64:
                    buffer_mgr.add_base64_pcm16(audio_b64)

                is_final_msg = msg_dict.get("is_final", False)
                audio_window = buffer_mgr.get_window() if not is_final_msg else buffer_mgr.flush()

                if audio_window is not None and len(audio_window) > 0:
                    # Run ASR
                    asr_res = asr_service.transcribe(audio_window, config.sample_rate)
                    ja_text = asr_res.get("text", "").strip()

                    if ja_text:
                        vi_text = translation_service.translate(ja_text)
                        latency = (time.time() - start_t) * 1000.0
                        resp = TranslationResponse(
                            id=str(uuid.uuid4())[:8],
                            ja_text=ja_text,
                            vi_text=vi_text,
                            is_final=is_final_msg,
                            confidence=asr_res.get("confidence", 0.9),
                            latency_ms=round(latency, 2)
                        )
                        last_result = (ja_text, vi_text, asr_res.get("confidence", 0.9), round(latency, 2))
                        await websocket.send_json(resp.model_dump())
                elif is_final_msg and last_result is not None:
                    # Flush had no new audio: deliver last partial as final so clients always get a final marker
                    ja_text, vi_text, confidence, latency = last_result
                    resp = TranslationResponse(
                        id=str(uuid.uuid4())[:8],
                        ja_text=ja_text,
                        vi_text=vi_text,
                        is_final=True,
                        confidence=confidence,
                        latency_ms=latency
                    )
                    await websocket.send_json(resp.model_dump())

    except WebSocketDisconnect:
        pass
    except Exception as e:
        log_error(f"WebSocket session error: {e}")
        try:
            await websocket.close()
        except Exception:
            pass
