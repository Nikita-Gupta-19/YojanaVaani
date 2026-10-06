"""
Speech API Endpoints for YojanaVaani (Phase 4).

Provides standalone speech endpoints:
- POST /stt: Upload an audio file, receive transcribed Hindi text + confidence score.
- POST /tts: Send Hindi text, receive synthesized vernacular audio (binary streaming or base64 JSON).
- GET  /tts: Convenient endpoint for quick browser playback and testing.
"""

import base64
import logging
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.services.asr_service import TranscriptionResult, get_asr_provider
from app.services.tts_service import get_tts_provider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Speech Services"])


class TTSRequestBody(BaseModel):
    """Request payload for text-to-speech synthesis."""
    text: str = Field(..., description="Hindi text to synthesize into spoken vernacular speech", min_length=1)
    language_code: str = Field(default="hi", description="Target ISO language code (default 'hi')")
    return_format: str = Field(
        default="binary",
        description="Response format: 'binary' for direct audio streaming or 'base64' for JSON payload"
    )


class TTSBase64Response(BaseModel):
    """JSON response for base64 audio requests."""
    audio_base64: str = Field(..., description="Base64-encoded audio bytes (MP3/WAV)")
    content_type: str = Field(default="audio/mpeg", description="MIME content type")
    text: str = Field(..., description="Original input text")
    language_code: str = Field(default="hi", description="Synthesized language code")


@router.post(
    "/stt",
    response_model=TranscriptionResult,
    summary="Transcribe spoken vernacular audio to Hindi text",
    description="Accepts an uploaded audio file (WAV, MP3, OGG, FLAC) and transcribes it via Whisper."
)
async def speech_to_text(
    file: UploadFile = File(..., description="Audio file payload"),
    language_code: str = Form(default="hi", description="Language code (default 'hi')")
) -> TranscriptionResult:
    """
    Transcribes uploaded audio into Hindi text.
    Returns text, confidence score, and low_confidence flag (True if confidence < 0.60).
    """
    if not file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No audio file uploaded.")

    try:
        audio_bytes = await file.read()
        if not audio_bytes or len(audio_bytes) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded audio file is empty.")

        asr = get_asr_provider()
        result = asr.transcribe(audio_bytes=audio_bytes, language_code=language_code)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /stt endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech transcription failed: {str(e)}"
        )


@router.post(
    "/tts",
    summary="Synthesize Hindi text into spoken vernacular audio",
    description="Converts text into spoken audio. Returns binary audio/mpeg by default, or base64 JSON if return_format='base64'."
)
async def text_to_speech(request: Request):
    """
    Synthesizes Hindi text into spoken audio bytes.
    Accepts input via JSON body or multipart form data.
    """
    content_type = request.headers.get("content-type", "").lower()
    target_text = None
    target_lang = "hi"
    target_format = "binary"

    if "application/json" in content_type:
        try:
            body = await request.json()
            target_text = body.get("text")
            target_lang = body.get("language_code", "hi")
            target_format = body.get("return_format", "binary")
        except Exception:
            pass
    elif "form" in content_type:
        try:
            form = await request.form()
            target_text = form.get("text")
            target_lang = form.get("language_code", "hi")
            target_format = form.get("return_format", "binary")
        except Exception:
            pass

    # Query param fallback if not found in body/form
    if not target_text:
        target_text = request.query_params.get("text")
        target_lang = request.query_params.get("language_code", target_lang or "hi")
        target_format = request.query_params.get("return_format", target_format or "binary")

    if not target_text or not str(target_text).strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text must not be empty."
        )
    target_text = str(target_text).strip()

    try:
        tts = get_tts_provider()
        audio_bytes = tts.synthesize(text=target_text.strip(), language_code=target_lang)

        if not audio_bytes:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Audio synthesis returned empty payload."
            )

        if target_format.lower() == "base64":
            b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
            return TTSBase64Response(
                audio_base64=b64_audio,
                content_type="audio/mpeg",
                text=target_text,
                language_code=target_lang
            )
        else:
            return Response(
                content=audio_bytes,
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": "inline; filename=yojanavaani_speech.mp3",
                    "Content-Length": str(len(audio_bytes))
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /tts endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech synthesis failed: {str(e)}"
        )


@router.get(
    "/tts",
    summary="GET endpoint for text-to-speech (in-browser audio playback)",
    description="Stream synthesized audio directly in browser or HTML5 audio players."
)
async def text_to_speech_get(
    text: str = Query(..., description="Hindi text to synthesize"),
    language_code: str = Query(default="hi", description="Language code")
):
    """Enables direct URL playback in audio tags or browser tabs."""
    tts = get_tts_provider()
    audio_bytes = tts.synthesize(text=text.strip(), language_code=language_code)
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline; filename=speech.mp3"}
    )
