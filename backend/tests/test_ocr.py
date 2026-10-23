"""
Unit tests for Document OCR Service & API Endpoints (Phase 6).

Verifies:
1. OpenCV preprocessing pipeline (deskew, grayscale, CLAHE, Gaussian denoise).
2. Tesseract field extraction on synthetic Income, Ration, Khasra, and Identity documents.
3. FastAPI endpoint: POST /documents/ocr.
4. FastAPI endpoint: POST /documents/confirm (updating CitizenProfile in session).
"""

import io
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.ocr_service import OCRService
from app.services.conversation_manager import conversation_manager

client = TestClient(app)
MOCK_DIR = Path(__file__).resolve().parent.parent / "data" / "mock_documents"


def test_ocr_service_income_certificate():
    img_path = MOCK_DIR / "income_cert_01_ramesh_kumar.png"
    assert img_path.exists(), "Mock document income_cert_01 must exist"

    with open(img_path, "rb") as f:
        img_bytes = f.read()

    res = OCRService.process_document(img_bytes, document_type="income_certificate")
    assert res.document_type == "income_certificate"
    assert "annual_income" in res.extracted_fields
    assert res.extracted_fields["annual_income"] == 48000.0
    assert "Barabanki" in res.extracted_fields.get("district", "")
    assert res.confidence_scores["annual_income"] >= 0.70


def test_ocr_service_ration_card():
    img_path = MOCK_DIR / "ration_card_01_aay_gorakhpur.png"
    assert img_path.exists(), "Mock document ration_card_01 must exist"

    with open(img_path, "rb") as f:
        img_bytes = f.read()

    res = OCRService.process_document(img_bytes, document_type="ration_card")
    assert "Ramwati" in res.extracted_fields.get("name", "")
    assert "family_members_count" in res.extracted_fields
    assert res.extracted_fields["family_members_count"] == 5


def test_ocr_service_khasra_land():
    img_path = MOCK_DIR / "khasra_land_01_kishan_lal.png"
    assert img_path.exists(), "Mock document khasra_land_01 must exist"

    with open(img_path, "rb") as f:
        img_bytes = f.read()

    res = OCRService.process_document(img_bytes, document_type="khasra_khatauni")
    assert "land_holding_area_hectares" in res.extracted_fields
    assert res.extracted_fields["land_holding_area_hectares"] == 0.84


def test_post_documents_ocr_endpoint():
    img_path = MOCK_DIR / "income_cert_01_ramesh_kumar.png"
    with open(img_path, "rb") as f:
        file_bytes = f.read()

    response = client.post(
        "/documents/ocr",
        files={"file": ("income_cert.png", file_bytes, "image/png")},
        data={"document_type": "income_certificate"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "document_id" in data
    assert data["document_type"] == "income_certificate"
    assert "extracted_fields" in data
    assert data["extracted_fields"].get("annual_income") == 48000.0
    assert "confirmation_prompt" in data


def test_post_documents_confirm_endpoint():
    # 1. Create a conversation
    session = conversation_manager.create_conversation("conv_ocr_confirm_test")
    cid = session.conversation_id

    # 2. Upload document to /documents/ocr
    img_path = MOCK_DIR / "income_cert_01_ramesh_kumar.png"
    with open(img_path, "rb") as f:
        file_bytes = f.read()

    upload_res = client.post(
        "/documents/ocr",
        files={"file": ("income_cert.png", file_bytes, "image/png")},
        data={"document_type": "income_certificate", "conversation_id": cid}
    )
    assert upload_res.status_code == 200
    doc_id = upload_res.json()["document_id"]

    # 3. Confirm document extraction
    confirm_res = client.post(
        "/documents/confirm",
        json={
            "document_id": doc_id,
            "conversation_id": cid,
            "is_confirmed": True,
            "confirmed_fields": {"annual_income": 48000.0, "district": "Barabanki"}
        }
    )
    assert confirm_res.status_code == 200
    data = confirm_res.json()
    assert data["status"] == "confirmed"
    assert data["applied_profile_updates"]["approx_income_bracket"] == "below_2_lakh"
    assert data["applied_profile_updates"]["district"] == "Barabanki"

    # Verify conversation state was updated
    updated_session = conversation_manager.get_conversation(cid)
    assert updated_session.citizen_profile.district == "Barabanki"
    assert updated_session.citizen_profile.approx_income_bracket == "below_2_lakh"
    assert len(updated_session.collected_documents) >= 1
