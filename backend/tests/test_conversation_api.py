"""
Unit tests for Conversation API Endpoints (Phase 7).

Verifies the unified conversational loop:
- POST /conversation/start
- POST /conversation/{id}/respond (text and audio payloads)
- POST /conversation/{id}/document (OCR processing)
- POST /conversation/{id}/confirm_document (profile update & re-evaluation)
- GET  /conversation/{id}
"""

import io
import json
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.conversation import ConversationStatus
from app.services.conversation_manager import conversation_manager

client = TestClient(app)


def test_start_conversation_endpoint():
    """Verify POST /conversation/start initializes a session with the 1st baseline question."""
    response = client.post("/conversation/start")
    assert response.status_code == 200
    data = response.json()

    assert "conversation_id" in data
    assert data["status"] == "baseline_interview"
    assert data["current_field"] == "name"
    assert data["question_index"] == 0
    assert data["total_questions"] == 9

    action = data["action"]
    assert action["type"] == "ask_question"
    assert "नाम" in action["text"]
    assert action["field_name"] == "name"
    assert "audio_url" in action


def test_respond_sequential_baseline_turns():
    """Verify POST /conversation/{id}/respond advances through the baseline interview."""
    # 1. Start conversation
    start_res = client.post("/conversation/start")
    cid = start_res.json()["conversation_id"]

    # 2. Answer Name
    res1 = client.post(f"/conversation/{cid}/respond", data={"text": "मेरा नाम रमेश कुमार है"})
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1["citizen_profile"]["name"] == "रमेश कुमार"
    assert d1["action"]["type"] == "ask_question"
    assert d1["action"]["field_name"] == "age"

    # 3. Answer Age
    res2 = client.post(f"/conversation/{cid}/respond", data={"text": "मेरी उम्र 38 साल है"})
    assert res2.status_code == 200
    d2 = res2.json()
    assert d2["citizen_profile"]["age"] == 38
    assert d2["action"]["field_name"] == "gender"

    # 4. Answer Gender
    res3 = client.post(f"/conversation/{cid}/respond", data={"text": "पुरुष"})
    assert res3.status_code == 200
    d3 = res3.json()
    assert d3["citizen_profile"]["gender"] == "Male"
    assert d3["action"]["field_name"] == "state_district"


def test_respond_audio_file_upload():
    """Verify POST /conversation/{id}/respond accepts an audio file upload via STT."""
    start_res = client.post("/conversation/start")
    cid = start_res.json()["conversation_id"]

    # Create synthetic WAV bytes
    import wave
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b'\x00\x00' * 8000)
    buf.seek(0)

    from unittest.mock import patch
    from app.services.asr_service import TranscriptionResult

    with patch("app.api.conversation.get_asr_provider") as mock_asr:
        mock_asr.return_value.transcribe.return_value = TranscriptionResult(
            text="सावित्री देवी",
            confidence=0.95,
            language_code="hi",
            low_confidence=False
        )
        files = {"file": ("response.wav", buf, "audio/wav")}
        res = client.post(f"/conversation/{cid}/respond", files=files)
        assert res.status_code == 200
        data = res.json()
        assert "transcribed_text" in data
        assert data["action"]["type"] == "ask_question"


def test_document_ocr_and_confirm_endpoints():
    """Verify document OCR and confirmation flow updates profile facts."""
    # 1. Create a session
    start_res = client.post("/conversation/start")
    cid = start_res.json()["conversation_id"]

    # 2. Upload synthetic mock income certificate image
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (300, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), "Income Certificate Annual Income: Rs 45000", fill=(0, 0, 0))
    img_buf = io.BytesIO()
    img.save(img_buf, format="PNG")
    img_buf.seek(0)

    files = {"file": ("mock_income.png", img_buf, "image/png")}
    ocr_res = client.post(
        f"/conversation/{cid}/document",
        files=files,
        data={"document_type": "income_certificate"}
    )
    assert ocr_res.status_code == 200
    ocr_data = ocr_res.json()
    assert ocr_data["conversation_id"] == cid
    assert ocr_data["document_type"] == "income_certificate"
    assert "extracted_fields" in ocr_data

    # 3. Confirm document fields
    confirm_res = client.post(
        f"/conversation/{cid}/confirm_document",
        data={
            "confirmed": True,
            "fields": json.dumps({"annual_income": 45000, "name": "Ramesh Kumar"})
        }
    )
    assert confirm_res.status_code == 200
    confirm_data = confirm_res.json()
    assert confirm_data["citizen_profile"]["approx_income_bracket"] == "below_2_lakh"
    assert confirm_data["citizen_profile"]["name"] == "Ramesh Kumar"
    assert confirm_data["action"]["type"] == "present_results"


def test_get_conversation_state():
    """Verify GET /conversation/{id} returns state and 404 for missing ID."""
    start_res = client.post("/conversation/start")
    cid = start_res.json()["conversation_id"]

    get_res = client.get(f"/conversation/{cid}")
    assert get_res.status_code == 200
    state = get_res.json()
    assert state["conversation_id"] == cid
    assert state["status"] == "baseline_interview"

    missing_res = client.get("/conversation/non_existent_uuid_12345")
    assert missing_res.status_code == 404


def test_get_conversation_report():
    """Verify GET /conversation/{id}/report returns structured citizen report."""
    start_res = client.post("/conversation/start")
    cid = start_res.json()["conversation_id"]

    # Confirm a document to populate collected_documents
    client.post(
        f"/conversation/{cid}/confirm_document",
        data={
            "confirmed": True,
            "fields": json.dumps({"annual_income": 45000, "name": "रमेश कुमार", "document_type": "income_certificate"})
        }
    )

    report_res = client.get(f"/conversation/{cid}/report")
    assert report_res.status_code == 200
    report = report_res.json()
    assert report["conversation_id"] == cid
    assert report["citizen_profile"]["name"] == "रमेश कुमार"


def test_document_upload_json_and_sample():
    """Verify POST /conversation/{id}/document with sample_key works seamlessly without manual file."""
    start_res = client.post("/conversation/start")
    cid = start_res.json()["conversation_id"]

    # Post JSON specifying sample_key
    res = client.post(
        f"/conversation/{cid}/document",
        json={"document_type": "income_certificate", "sample_key": "income_certificate"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["conversation_id"] == cid
    assert data["document_type"] == "income_certificate"
    assert "annual_income" in data["extracted_fields"]
    assert data["extracted_fields"]["annual_income"] in [48000, 60000, "48000", "60000"]
    assert data["mean_confidence"] > 0.80


def test_edit_conversation_answer():
    """Verify POST /conversation/{id}/edit_answer updates a specific field without wiping out other fields."""
    start_res = client.post("/conversation/start")
    cid = start_res.json()["conversation_id"]

    # Initial answer for name
    client.post(f"/conversation/{cid}/respond", json={"text": "रामवती देवी"})

    # Initial answer for age
    client.post(f"/conversation/{cid}/respond", json={"text": "35 साल"})

    # Verify initial profile
    get_res = client.get(f"/conversation/{cid}")
    prof = get_res.json()["citizen_profile"]
    assert prof["name"] == "रामवती देवी"
    assert prof["age"] == 35

    # Edit age to 45 years without affecting name
    edit_res = client.post(
        f"/conversation/{cid}/edit_answer",
        json={"field_name": "age", "text": "45 साल"}
    )
    assert edit_res.status_code == 200
    edit_data = edit_res.json()
    assert edit_data["citizen_profile"]["age"] == 45
    assert edit_data["citizen_profile"]["name"] == "रामवती देवी"

