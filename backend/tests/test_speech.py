"""
Unit tests for Hindi Speech-to-Text (STT) and Text-to-Speech (TTS) endpoints — Phase 4.
"""

import pytest
import io
import soundfile as sf
import numpy as np
from fastapi.testclient import TestClient
from app.main import app
from app.services.tts_service import GoogleHindiTTSProvider, get_tts_provider
from app.services.asr_service import TranscriptionResult, get_asr_provider

client = TestClient(app)


def test_tts_provider_direct():
    """Verify TTS synthesizer generates non-empty audio payload."""
    tts = GoogleHindiTTSProvider()
    audio_bytes = tts.synthesize("नमस्ते, आपका स्वागत है।", language_code="hi")
    assert len(audio_bytes) > 500, "Synthesized audio is too small"


def test_post_tts_binary_endpoint():
    """Verify POST /tts returns streaming audio/mpeg response."""
    response = client.post(
        "/tts",
        json={"text": "आपकी उम्र कितनी है?", "language_code": "hi", "return_format": "binary"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert len(response.content) > 500


def test_post_tts_base64_endpoint():
    """Verify POST /tts with return_format='base64' returns valid JSON."""
    response = client.post(
        "/tts",
        json={"text": "उत्तर प्रदेश", "language_code": "hi", "return_format": "base64"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "audio_base64" in data
    assert len(data["audio_base64"]) > 500
    assert data["language_code"] == "hi"


def test_post_stt_endpoint():
    """Verify POST /stt processes an uploaded audio file and returns transcription."""
    # 1. Synthesize real audio to test STT endpoint
    tts = get_tts_provider()
    audio_bytes = tts.synthesize("मेरा नाम रामवती देवी है", language_code="hi")

    # 2. Upload to /stt
    files = {"file": ("test_name.mp3", audio_bytes, "audio/mpeg")}
    data = {"language_code": "hi"}
    response = client.post("/stt", files=files, data=data)

    assert response.status_code == 200
    res_json = response.json()
    assert "text" in res_json
    assert "confidence" in res_json
    assert "low_confidence" in res_json
    assert isinstance(res_json["confidence"], float)
    assert 0.0 <= res_json["confidence"] <= 1.0


def test_post_stt_empty_file_error():
    """Verify POST /stt rejects empty audio payload with 400 Bad Request."""
    files = {"file": ("empty.mp3", b"", "audio/mpeg")}
    response = client.post("/stt", files=files)
    assert response.status_code == 400
