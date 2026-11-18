"""
Conversation API Endpoints for YojanaVaani (Phase 7 Mobile App Integration).

Provides a unified "send audio/action, receive next action" loop for the mobile client:
- POST /conversation/start: Initiates a session and returns the 1st baseline question + audio.
- POST /conversation/{id}/respond: Accepts spoken audio or text answer, runs STT, records answer,
  and returns the NEXT action (ask_question, present_results, request_document, or escalate).
- POST /conversation/{id}/document: Accepts uploaded document photo, runs OCR, returns extracted fields.
- POST /conversation/{id}/confirm_document: Accepts citizen confirmation, updates profile, and returns next action.
- GET  /conversation/{id}: Inspects complete conversational state.
"""

import asyncio
import base64
import concurrent.futures
from datetime import datetime, timezone
import json
import logging
import os
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from fastapi import APIRouter, File, Form, HTTPException, Query, Request, UploadFile, status
from pydantic import BaseModel, Field

from app.models.conversation import ConversationState, ConversationStatus
from app.services.asr_service import get_asr_provider
from app.services.baseline_interview import (
    TOTAL_BASELINE_QUESTIONS,
    get_question_by_index,
)
from app.services.conversation_manager import conversation_manager
from app.services.eligibility_engine import EligibilityEngine
from app.services.ocr_service import OCRService
from app.services.tts_service import get_tts_provider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversation", tags=["Conversational Flow"])


# -----------------------------------------------------------------------------
# PYDANTIC RESPONSE SCHEMAS
# -----------------------------------------------------------------------------

class ActionPayload(BaseModel):
    """Structured action directive instructing the mobile client on what screen/UI to display next."""
    type: str = Field(..., description="Action type: ask_question | present_results | request_document | escalate")
    text: str = Field(..., description="Spoken Hindi prompt text")
    field_name: Optional[str] = Field(default=None, description="Current citizen profile field being collected")
    audio_url: Optional[str] = Field(default=None, description="Direct URL to stream synthesized audio")
    audio_base64: Optional[str] = Field(default=None, description="Base64-encoded audio bytes for immediate offline/low-latency playback")
    document_type: Optional[str] = Field(default=None, description="Type of document requested if type == 'request_document'")
    schemes: Optional[List[Dict[str, Any]]] = Field(default=None, description="Ranked scheme candidates if type == 'present_results'")
    csc_info: Optional[Dict[str, Any]] = Field(default=None, description="CSC Kiosk details if type == 'escalate'")
    options: Optional[List[str]] = Field(default=None, description="Quick answer suggestion chips for citizen convenience")


class ConversationStartResponse(BaseModel):
    """Response returned when a citizen starts a new voice navigation session."""
    conversation_id: str
    status: str
    current_field: str
    question_index: int
    total_questions: int
    action: ActionPayload


class ConversationTurnResponse(BaseModel):
    """Response returned upon answering a baseline question or follow-up."""
    conversation_id: str
    status: str
    transcribed_text: Optional[str] = None
    citizen_profile: Dict[str, Any]
    action: ActionPayload
    question_index: Optional[int] = None
    total_questions: Optional[int] = 9


class DocumentOCRResponse(BaseModel):
    """Response returned after running OpenCV + Tesseract OCR on an uploaded document."""
    conversation_id: str
    document_type: str
    extracted_fields: Dict[str, Any]
    confidence_scores: Dict[str, float]
    mean_confidence: float
    is_valid: bool
    raw_text: str


class CitizenReportResponse(BaseModel):
    """Complete structured profile and application report for the citizen."""
    conversation_id: str
    citizen_profile: Dict[str, Any]
    stated_need: Optional[str] = None
    collected_documents: List[Dict[str, Any]] = Field(default_factory=list)
    recommended_schemes: List[Dict[str, Any]] = Field(default_factory=list)
    selected_scheme: Optional[Dict[str, Any]] = None
    report_text_hindi: str
    audio_base64: Optional[str] = None
    generated_at: str


# -----------------------------------------------------------------------------
# HELPER: Audio Synthesis
# -----------------------------------------------------------------------------

_tts_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)


def _synthesize_audio_base64(text: str) -> Optional[str]:
    """Helper to synthesize Hindi text to base64 audio string via TTS provider with safe 5.0s timeout."""
    def _do_synth():
        try:
            tts = get_tts_provider()
            audio_bytes = tts.synthesize(text=text.strip(), language_code="hi")
            if audio_bytes:
                return base64.b64encode(audio_bytes).decode("utf-8")
        except Exception as e:
            logger.warning(f"Could not synthesize audio for text: {e}")
        return None

    try:
        future = _tts_executor.submit(_do_synth)
        return future.result(timeout=5.0)
    except concurrent.futures.TimeoutError:
        logger.warning(f"TTS synthesis timed out after 5.0s for text: {text[:30]}...")
        return None
    except Exception as e:
        logger.warning(f"Error executing TTS synthesis: {e}")
        return None


# -----------------------------------------------------------------------------
# ENDPOINT 1: POST /conversation/start
# -----------------------------------------------------------------------------

@router.post(
    "/start",
    response_model=ConversationStartResponse,
    summary="Start a new voice navigation session",
    description="Initializes session and returns 1st baseline interview question (spoken Hindi audio + text)."
)
async def start_conversation(
    conversation_id: Optional[str] = Query(None, description="Optional custom conversation ID")
) -> ConversationStartResponse:
    conv = conversation_manager.create_conversation(conversation_id)
    first_q = get_question_by_index(0)

    if not first_q:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Baseline questions configuration missing."
        )

    q_text = first_q.hindi_text
    audio_b64 = _synthesize_audio_base64(q_text)
    audio_stream_url = f"/tts?text={quote(q_text)}&language_code=hi"

    action = ActionPayload(
        type="ask_question",
        text=q_text,
        field_name=first_q.field_name,
        audio_url=audio_stream_url,
        audio_base64=audio_b64,
        options=list(first_q.sample_answers) if first_q.sample_answers else None
    )

    return ConversationStartResponse(
        conversation_id=conv.conversation_id,
        status=conv.status.value,
        current_field=first_q.field_name,
        question_index=0,
        total_questions=TOTAL_BASELINE_QUESTIONS,
        action=action
    )


# -----------------------------------------------------------------------------
# ENDPOINT 2: POST /conversation/{id}/respond
# -----------------------------------------------------------------------------

@router.post(
    "/{id}/respond",
    response_model=ConversationTurnResponse,
    summary="Submit citizen spoken or text response",
    description="Accepts spoken audio (WAV/MP3/M4A) or text, transcribes via STT, records answer, and emits next action."
)
async def respond_to_conversation(
    id: str,
    request: Request,
    file: Optional[UploadFile] = File(None, description="Audio recording of citizen's spoken response"),
    text: Optional[str] = Form(None, description="Optional direct text answer for fallback/text entry")
) -> ConversationTurnResponse:
    conv = conversation_manager.get_conversation(id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation ID '{id}' not found."
        )

    spoken_text: str = ""

    # Check multipart audio upload
    if file:
        try:
            audio_bytes = await file.read()
            if audio_bytes and len(audio_bytes) > 0:
                asr = get_asr_provider()
                trans_result = await asyncio.to_thread(asr.transcribe, audio_bytes, "hi")
                if trans_result and not trans_result.low_confidence and trans_result.text.strip():
                    spoken_text = trans_result.text.strip()
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="आपकी आवाज़ स्पष्ट सुनाई नहीं दी। कृपया दोबारा बोलें या नीचे लिखकर बताएं।"
                    )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error transcribing uploaded audio for conversation {id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Audio transcription failed: {str(e)}"
            )

    # Check direct text form or JSON body fallback (text or audio_base64)
    if not spoken_text:
        if text and text.strip():
            spoken_text = text.strip()
        elif "application/json" in request.headers.get("content-type", "").lower():
            try:
                body = await request.json()
                spoken_text = body.get("text", "").strip()
                if not spoken_text and body.get("audio_base64"):
                    audio_b64 = body["audio_base64"]
                    audio_bytes = base64.b64decode(audio_b64)
                    if audio_bytes and len(audio_bytes) > 0:
                        asr = get_asr_provider()
                        trans_result = await asyncio.to_thread(asr.transcribe, audio_bytes, "hi")
                        if trans_result and not trans_result.low_confidence and trans_result.text.strip():
                            spoken_text = trans_result.text.strip()
                        else:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="आपकी आवाज़ स्पष्ट सुनाई नहीं दी। कृपया दोबारा बोलें या नीचे लिखकर बताएं।"
                            )
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Failed to parse JSON body or transcribe audio_base64: {e}")

    if not spoken_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="उत्तर प्राप्त नहीं हुआ। कृपया बोलें या नीचे दिए गए बॉक्स में लिखकर भेजें।"
        )

    current_q = conversation_manager.get_current_question_metadata(id)
    current_field = current_q.field_name if current_q else "stated_need"

    # Record turn via ConversationManager
    conv = conversation_manager.record_answer(id, current_field, spoken_text)

    # CASE A: Stage 1 Baseline Interview in Progress
    if conv.status == ConversationStatus.baseline_interview:
        next_q = conversation_manager.get_current_question_metadata(id)
        if next_q:
            q_text = next_q.hindi_text
            audio_b64 = _synthesize_audio_base64(q_text)
            action = ActionPayload(
                type="ask_question",
                text=q_text,
                field_name=next_q.field_name,
                audio_url=f"/tts?text={quote(q_text)}&language_code=hi",
                audio_base64=audio_b64,
                options=list(next_q.sample_answers) if next_q.sample_answers else None
            )
            return ConversationTurnResponse(
                conversation_id=conv.conversation_id,
                status=conv.status.value,
                transcribed_text=spoken_text,
                citizen_profile=conv.citizen_profile.model_dump(),
                action=action,
                question_index=conv.current_question_index,
                total_questions=9
            )

    # CASE B: Stage 1 Completed -> Stage 2 Agentic Follow-Up Loop
    if conv.status == ConversationStatus.scheme_matching:
        conv = conversation_manager.run_agentic_followup(id)

    last_assistant_turn = ""
    for turn in reversed(conv.conversation_history):
        if turn.speaker == "assistant":
            last_assistant_turn = turn.text
            break

    # Action Determination based on agent status
    if conv.status == ConversationStatus.results_ready:
        speech_text = last_assistant_turn or "आपकी पात्रता के अनुकूल योजनाएं प्राप्त हो गई हैं।"
        audio_b64 = _synthesize_audio_base64(speech_text)
        action = ActionPayload(
            type="present_results",
            text=speech_text,
            schemes=conv.candidate_schemes,
            audio_url=f"/tts?text={quote(speech_text)}&language_code=hi",
            audio_base64=audio_b64
        )
    elif conv.status == ConversationStatus.awaiting_document:
        doc_type = conv.missing_facts[0] if conv.missing_facts else "income_certificate"
        speech_text = last_assistant_turn or "कृपया पात्रता सत्यापन के लिए अपने दस्तावेज़ की फोटो खींचें।"
        audio_b64 = _synthesize_audio_base64(speech_text)
        action = ActionPayload(
            type="request_document",
            text=speech_text,
            document_type=doc_type,
            audio_url=f"/tts?text={quote(speech_text)}&language_code=hi",
            audio_base64=audio_b64
        )
    elif conv.status == ConversationStatus.escalated:
        speech_text = last_assistant_turn or "यह प्रश्न अधिक जटिल है। कृपया निकटतम कॉमन सर्विस सेंटर (CSC) पर जाएं।"
        audio_b64 = _synthesize_audio_base64(speech_text)
        action = ActionPayload(
            type="escalate",
            text=speech_text,
            csc_info={
                "csc_name": "Haidergarh Digital Seva Kendra",
                "helpline": "1800-3000-3468",
                "address": "Near Tehsil Complex, Haidergarh, Barabanki, UP - 225126",
                "timings": "09:00 AM - 05:00 PM (Monday to Saturday)"
            },
            audio_url=f"/tts?text={quote(speech_text)}&language_code=hi",
            audio_base64=audio_b64
        )
    else:
        # Default fallback to presenting results
        speech_text = last_assistant_turn or "सत्यापन पूर्ण हुआ।"
        audio_b64 = _synthesize_audio_base64(speech_text)
        action = ActionPayload(
            type="present_results",
            text=speech_text,
            schemes=conv.candidate_schemes,
            audio_url=f"/tts?text={quote(speech_text)}&language_code=hi",
            audio_base64=audio_b64
        )

    return ConversationTurnResponse(
        conversation_id=conv.conversation_id,
        status=conv.status.value,
        transcribed_text=spoken_text,
        citizen_profile=conv.citizen_profile.model_dump(),
        action=action,
        question_index=conv.current_question_index,
        total_questions=9
    )


# -----------------------------------------------------------------------------
# ENDPOINT 2B: POST /conversation/{id}/back
# -----------------------------------------------------------------------------

@router.post(
    "/{id}/back",
    response_model=ConversationTurnResponse,
    summary="Go back to the previous baseline interview question",
    description="Rolls back conversation state by one step so the citizen can correct or re-record their answer."
)
async def go_back_conversation(id: str) -> ConversationTurnResponse:
    conv = conversation_manager.go_back(id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation ID '{id}' not found."
        )

    prev_q = get_question_by_index(conv.current_question_index)
    if not prev_q:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Question metadata missing."
        )

    q_text = prev_q.hindi_text
    audio_b64 = _synthesize_audio_base64(q_text)
    action = ActionPayload(
        type="ask_question",
        text=q_text,
        field_name=prev_q.field_name,
        audio_url=f"/tts?text={quote(q_text)}&language_code=hi",
        audio_base64=audio_b64,
        options=list(prev_q.sample_answers) if prev_q.sample_answers else None
    )

    return ConversationTurnResponse(
        conversation_id=conv.conversation_id,
        status=conv.status.value,
        transcribed_text=None,
        citizen_profile=conv.citizen_profile.model_dump(),
        action=action,
        question_index=conv.current_question_index,
        total_questions=9
    )


# -----------------------------------------------------------------------------
# ENDPOINT 3: POST /conversation/{id}/document
# -----------------------------------------------------------------------------

@router.post(
    "/{id}/document",
    response_model=DocumentOCRResponse,
    summary="Upload document photo for OCR extraction",
    description="Processes document image via OpenCV deskew/CLAHE + Tesseract Devanagari OCR and returns fields for confirmation."
)
async def upload_document_photo(
    id: str,
    request: Request,
    file: Optional[UploadFile] = File(None, description="Document photograph image file (PNG/JPG)"),
    document_type: Optional[str] = Form(None, description="Optional document type hint (income_certificate, ration_card, etc.)"),
    sample_key: Optional[str] = Form(None, description="Key of synthetic sample document in backend/data/mock_documents/")
) -> DocumentOCRResponse:
    conv = conversation_manager.get_conversation(id)
    if not conv:
        conv = conversation_manager.create_conversation(id)

    content_type = request.headers.get("content-type", "")
    req_doc_type = document_type
    req_sample_key = sample_key
    req_is_sample = None
    image_bytes: Optional[bytes] = None

    # Handle application/json requests
    if "application/json" in content_type:
        try:
            body = await request.json()
            if not req_doc_type and "document_type" in body:
                req_doc_type = body["document_type"]
            if not req_sample_key and "sample_key" in body:
                req_sample_key = body["sample_key"]
            if "is_sample" in body:
                req_is_sample = bool(body["is_sample"])
            if "image_base64" in body and body["image_base64"]:
                import base64
                raw_b64 = body["image_base64"]
                if "," in raw_b64:
                    raw_b64 = raw_b64.split(",", 1)[1]
                image_bytes = base64.b64decode(raw_b64)
        except Exception as e:
            logger.warning(f"Error parsing JSON in upload_document_photo: {e}")

    # Handle multipart file upload if present
    if image_bytes is None and file is not None:
        try:
            image_bytes = await file.read()
        except Exception as e:
            logger.warning(f"Error reading uploaded file: {e}")

    # Fallback to synthetic mock documents if on emulator or sample requested
    if req_sample_key:
        doc_type_canonical = req_sample_key.lower()
    else:
        doc_type_canonical = (req_doc_type or "income_certificate").lower()

    # Determine whether user selected a predefined sample document or captured a real photo
    is_predefined_sample = bool(req_sample_key or (req_is_sample is True) or (not image_bytes))

    if not image_bytes or len(image_bytes) == 0:
        mock_map = {
            "income_certificate": "income_cert_01_ramesh_kumar.png",
            "income": "income_cert_01_ramesh_kumar.png",
            "ration_card": "ration_card_01_aay_gorakhpur.png",
            "ration": "ration_card_01_aay_gorakhpur.png",
            "khasra_khatauni": "khasra_land_01_kishan_lal.png",
            "land_record": "khasra_land_01_kishan_lal.png",
            "khasra": "khasra_land_01_kishan_lal.png",
            "aadhaar_card": "aadhaar_card_01_priya_sharma.png",
            "aadhaar": "aadhaar_card_01_priya_sharma.png",
            "identity": "aadhaar_card_01_priya_sharma.png",
        }
        chosen_sample = mock_map.get(req_sample_key or doc_type_canonical, "income_cert_01_ramesh_kumar.png")
        sample_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "mock_documents", chosen_sample)
        if not os.path.exists(sample_path):
            sample_path = os.path.join(os.getcwd(), "backend", "data", "mock_documents", chosen_sample)

        if os.path.exists(sample_path):
            with open(sample_path, "rb") as f:
                image_bytes = f.read()
            logger.info(f"Using synthetic mock document for OCR: {chosen_sample} ({len(image_bytes)} bytes)")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No image provided and mock document not found."
            )

    # For predefined sample documents: pass citizen profile name so sample details match user
    # For real photo captures: pass citizen_name=None so details are fetched genuinely from the scanned doc
    citizen_name = conv.citizen_profile.name if (is_predefined_sample and conv.citizen_profile) else None
    result = OCRService.process_document(
        image_bytes=image_bytes,
        document_type=doc_type_canonical,
        citizen_name=citizen_name
    )

    extracted_fields = dict(result.extracted_fields)
    confidence_scores = dict(result.confidence_scores)
    p = conv.citizen_profile

    # Enrich extracted fields with citizen profile facts ONLY if user selected predefined sample docs:
    if is_predefined_sample and p:
        if p.name and p.name not in ["नागरिक", "Unknown"]:
            extracted_fields["name"] = p.name
            confidence_scores["name"] = 0.95
        if "gender" not in extracted_fields and p.gender:
            extracted_fields["gender"] = p.gender
            confidence_scores["gender"] = 0.90
        if "income" in doc_type_canonical and "annual_income" not in extracted_fields:
            inc_val = getattr(p, "annual_income", None) or 48000
            extracted_fields["annual_income"] = float(inc_val)
            confidence_scores["annual_income"] = 0.88
        if ("aadhaar" in doc_type_canonical or "identity" in doc_type_canonical) and "aadhaar_number" not in extracted_fields:
            extracted_fields["aadhaar_number"] = "XXXX-XXXX-8812"
            confidence_scores["aadhaar_number"] = 0.94
        if ("bank" in doc_type_canonical or "passbook" in doc_type_canonical) and "account_number" not in extracted_fields:
            extracted_fields["bank_name"] = "State Bank of India (भारतीय स्टेट बैंक)"
            extracted_fields["account_number"] = "XXXX-XXXX-4589"
            extracted_fields["ifsc_code"] = "SBIN0001234"
            confidence_scores["bank_name"] = 0.95
            confidence_scores["account_number"] = 0.94
            confidence_scores["ifsc_code"] = 0.96
        if ("caste" in doc_type_canonical) and "social_category" not in extracted_fields:
            extracted_fields["social_category"] = p.social_category or "OBC"
            extracted_fields["certificate_number"] = "UP-CST-2026-88741"
            confidence_scores["social_category"] = 0.95
            confidence_scores["certificate_number"] = 0.92
        if ("disability" in doc_type_canonical or "divyang" in doc_type_canonical) and "disability_percentage" not in extracted_fields:
            extracted_fields["disability_percentage"] = "80%"
            extracted_fields["udid_number"] = "UP7894561230"
            confidence_scores["disability_percentage"] = 0.96
            confidence_scores["udid_number"] = 0.94

    # If OCR extracted 0 fields from a predefined sample, supply baseline profile verification fields
    if len(extracted_fields) == 0 and is_predefined_sample:
        logger.info(f"OCR returned 0 fields from uploaded photo for conversation {id}. Supplying baseline profile verification fields.")
        if "income" in doc_type_canonical:
            inc_val = getattr(p, "annual_income", None) or 48000
            extracted_fields["annual_income"] = float(inc_val)
            confidence_scores["annual_income"] = 0.88
            if p and p.name:
                extracted_fields["name"] = p.name
                confidence_scores["name"] = 0.85
            if p and p.district:
                extracted_fields["district"] = p.district
                confidence_scores["district"] = 0.85
        elif "ration" in doc_type_canonical:
            extracted_fields["ration_card_number"] = "215487963214"
            extracted_fields["card_category"] = "AAY"
            extracted_fields["family_members_count"] = 5
            confidence_scores["ration_card_number"] = 0.88
            confidence_scores["card_category"] = 0.88
            confidence_scores["family_members_count"] = 0.85
            if p and p.name:
                extracted_fields["name"] = p.name
                confidence_scores["name"] = 0.85
        elif "khasra" in doc_type_canonical or "land" in doc_type_canonical:
            extracted_fields["land_holding_area_hectares"] = 0.84
            extracted_fields["khasra_number"] = "42/2"
            confidence_scores["land_holding_area_hectares"] = 0.88
            confidence_scores["khasra_number"] = 0.88
            if p and p.name:
                extracted_fields["name"] = p.name
                confidence_scores["name"] = 0.85
        elif "bank" in doc_type_canonical or "passbook" in doc_type_canonical:
            extracted_fields["bank_name"] = "State Bank of India (भारतीय स्टेट बैंक)"
            extracted_fields["account_number"] = "XXXX-XXXX-4589"
            extracted_fields["ifsc_code"] = "SBIN0001234"
            confidence_scores["bank_name"] = 0.95
            confidence_scores["account_number"] = 0.94
            confidence_scores["ifsc_code"] = 0.96
            if p and p.name:
                extracted_fields["name"] = p.name
                confidence_scores["name"] = 0.92
        elif "caste" in doc_type_canonical:
            extracted_fields["social_category"] = (p and p.social_category) or "OBC"
            extracted_fields["certificate_number"] = "UP-CST-2026-88741"
            confidence_scores["social_category"] = 0.95
            confidence_scores["certificate_number"] = 0.92
            if p and p.name:
                extracted_fields["name"] = p.name
                confidence_scores["name"] = 0.90
        elif "disability" in doc_type_canonical or "divyang" in doc_type_canonical:
            extracted_fields["disability_percentage"] = "80%"
            extracted_fields["udid_number"] = "UP7894561230"
            confidence_scores["disability_percentage"] = 0.95
            confidence_scores["udid_number"] = 0.94
            if p and p.name:
                extracted_fields["name"] = p.name
                confidence_scores["name"] = 0.90
        elif "domicile" in doc_type_canonical:
            extracted_fields["domicile_state"] = (p and p.state) or "Uttar Pradesh"
            extracted_fields["certificate_number"] = "UP-DOM-2026-44120"
            confidence_scores["domicile_state"] = 0.94
            confidence_scores["certificate_number"] = 0.92
        else:
            if p and p.name:
                extracted_fields["name"] = p.name
                confidence_scores["name"] = 0.88
            if p and p.gender:
                extracted_fields["gender"] = p.gender
                confidence_scores["gender"] = 0.88
            if p and p.district:
                extracted_fields["district"] = p.district
                confidence_scores["district"] = 0.88
            extracted_fields["aadhaar_number"] = "XXXX-XXXX-1100"
            confidence_scores["aadhaar_number"] = 0.88

    confs = list(confidence_scores.values())
    mean_conf = float(sum(confs) / len(confs)) if confs else 0.85
    is_valid = bool(len(extracted_fields) > 0 and mean_conf >= 0.70)

    # Return canonical document type requested by caller if specific, else detected type
    final_doc_type = doc_type_canonical if (doc_type_canonical and doc_type_canonical != "generic") else result.document_type

    return DocumentOCRResponse(
        conversation_id=id,
        document_type=final_doc_type,
        extracted_fields=extracted_fields,
        confidence_scores=confidence_scores,
        mean_confidence=round(mean_conf, 3),
        is_valid=is_valid,
        raw_text=result.raw_ocr_text[:400] if result.raw_ocr_text else "दस्तावेज़ स्कैनिंग पूर्ण"
    )


# -----------------------------------------------------------------------------
# ENDPOINT 4: POST /conversation/{id}/confirm_document
# -----------------------------------------------------------------------------

@router.post(
    "/{id}/confirm_document",
    response_model=ConversationTurnResponse,
    summary="Confirm or correct extracted document fields",
    description="Accepts citizen confirmation, updates profile, re-evaluates eligibility rules, and emits next action."
)
async def confirm_document_fields(
    id: str,
    request: Request,
    confirmed: bool = Form(True, description="Whether citizen confirms extracted fields are accurate"),
    fields: Optional[str] = Form(None, description="JSON string of confirmed/corrected fields")
) -> ConversationTurnResponse:
    conv = conversation_manager.get_conversation(id)
    if not conv:
        conv = conversation_manager.create_conversation(id)

    confirmed_fields: Dict[str, Any] = {}
    if fields:
        try:
            confirmed_fields = json.loads(fields)
        except Exception:
            pass
    else:
        # Check if sent via JSON body
        try:
            body = await request.json()
            confirmed = body.get("confirmed", confirmed)
            confirmed_fields = body.get("fields", {})
        except Exception:
            pass

    # If citizen confirms, merge verified facts into CitizenProfile
    if confirmed and confirmed_fields:
        profile = conv.citizen_profile

        # Update Income
        if "annual_income" in confirmed_fields:
            val = confirmed_fields["annual_income"]
            try:
                income_num = float(val)
                if income_num <= 200000:
                    profile.approx_income_bracket = "below_2_lakh"
                elif income_num <= 500000:
                    profile.approx_income_bracket = "2_to_5_lakh"
                else:
                    profile.approx_income_bracket = "above_5_lakh"
            except (ValueError, TypeError):
                pass

        # Update Name only if citizen profile name was not already established
        if "name" in confirmed_fields and isinstance(confirmed_fields["name"], str):
            clean_name = confirmed_fields["name"].strip()
            # Protect interview name: NEVER overwrite if interview profile established the citizen's real name
            if clean_name and (not profile.name or profile.name in ["नागरिक", "नागरिक (सत्यापित)", "Unknown"]):
                profile.name = clean_name

        # Update Location / State
        if "state" in confirmed_fields and isinstance(confirmed_fields["state"], str):
            profile.state = confirmed_fields["state"].strip()
        if "district" in confirmed_fields and isinstance(confirmed_fields["district"], str):
            profile.district = confirmed_fields["district"].strip()

        # Update Gender if present
        if "gender" in confirmed_fields and isinstance(confirmed_fields["gender"], str):
            profile.gender = confirmed_fields["gender"].strip()

        # Record verified document record
        doc_fields = dict(confirmed_fields)
        if "name" not in doc_fields and profile.name and profile.name not in ["नागरिक", "नागरिक (सत्यापित)", "Unknown"]:
            doc_fields["name"] = profile.name

        doc_entry = {
            "document_type": confirmed_fields.get("document_type") or "verified_document",
            "extracted_fields": doc_fields,
            "verification_status": "verified" if confirmed else "unverified",
            "confidence_score": confirmed_fields.get("confidence", 0.94),
            "confirmed_at": datetime.now(timezone.utc).isoformat()
        }
        conv.collected_documents.append(doc_entry)

    # Re-evaluate candidate schemes deterministically with updated profile
    if conv.candidate_schemes:
        ranked_verdicts = EligibilityEngine.evaluate_and_rank_candidates(
            profile=conv.citizen_profile.model_dump(),
            candidate_schemes=conv.candidate_schemes
        )
        updated_schemes = []
        for v in ranked_verdicts:
            for s in conv.candidate_schemes:
                if s.get("id") == v.scheme_id:
                    s_copy = dict(s)
                    s_copy["verdict"] = v.verdict.value
                    s_copy["reason"] = v.overall_reason
                    s_copy["disqualification_reasons"] = v.disqualification_reasons
                    s_copy["missing_fields"] = v.missing_fields
                    s_copy["manual_review_flags"] = v.manual_review_flags
                    updated_schemes.append(s_copy)
                    break
        conv.candidate_schemes = updated_schemes

    conv.status = ConversationStatus.results_ready
    speech_text = "दस्तावेज़ सत्यापन पूर्ण हुआ। आपकी पात्रता का नवीनीकरण कर दिया गया है।"
    audio_b64 = _synthesize_audio_base64(speech_text)

    conversation_manager._save_to_disk()

    action = ActionPayload(
        type="present_results",
        text=speech_text,
        schemes=conv.candidate_schemes,
        audio_url=f"/tts?text={quote(speech_text)}&language_code=hi",
        audio_base64=audio_b64
    )

    return ConversationTurnResponse(
        conversation_id=conv.conversation_id,
        status=conv.status.value,
        transcribed_text="दस्तावेज़ सत्यापित (Confirmed)",
        citizen_profile=conv.citizen_profile.model_dump(),
        action=action
    )


# -----------------------------------------------------------------------------
# ENDPOINT 4B: GET /conversation/history
# -----------------------------------------------------------------------------

@router.get(
    "/history",
    response_model=List[Dict[str, Any]],
    summary="Get history of all citizen conversations and saved assessments",
    description="Returns all previously stored sessions, citizen profiles, and recommended schemes."
)
async def get_all_conversation_history() -> List[Dict[str, Any]]:
    conversations = conversation_manager.get_all_conversations()
    results = []
    for conv in conversations:
        results.append({
            "conversation_id": conv.conversation_id,
            "status": conv.status.value if hasattr(conv.status, "value") else str(conv.status),
            "citizen_profile": conv.citizen_profile.model_dump(),
            "stated_need": conv.stated_need,
            "recommended_schemes_count": len(conv.candidate_schemes),
            "recommended_schemes": conv.candidate_schemes,
            "collected_documents_count": len(conv.collected_documents),
            "collected_documents": conv.collected_documents,
            "turns_count": len(conv.conversation_history),
        })
    return results


@router.delete(
    "/history",
    summary="Clear all conversation and assessment history",
    description="Wipes all saved citizen assessments and conversational sessions completely."
)
async def delete_all_conversation_history() -> Dict[str, Any]:
    conversation_manager.clear_all_history()
    return {"status": "success", "message": "All user conversation history has been permanently cleared."}


@router.delete(
    "/{id}",
    summary="Delete a single conversation session from history",
    description="Removes a specific citizen assessment record from saved history."
)
async def delete_single_conversation(id: str) -> Dict[str, Any]:
    success = conversation_manager.delete_conversation(id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation session with id '{id}' not found."
        )
    return {"status": "success", "message": f"Conversation session '{id}' deleted successfully."}


# -----------------------------------------------------------------------------
# ENDPOINT 5: GET /conversation/{id}
# -----------------------------------------------------------------------------

@router.get(
    "/{id}",
    response_model=ConversationState,
    summary="Get full conversation state",
    description="Returns current citizen profile, conversation history, and matched candidate schemes."
)
async def get_conversation_state(id: str) -> ConversationState:
    conv = conversation_manager.get_conversation(id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation ID '{id}' not found."
        )
    return conv


# -----------------------------------------------------------------------------
# ENDPOINT 6: GET /conversation/{id}/report
# -----------------------------------------------------------------------------

@router.get(
    "/{id}/report",
    response_model=CitizenReportResponse,
    summary="Generate complete citizen profile and application report",
    description="Compiles verified citizen details, scanned documents, and recommended scheme into a complete audio-visual report."
)
async def get_conversation_report(
    id: str,
    scheme_id: Optional[int] = Query(None, description="Optional target scheme ID selected by citizen")
) -> CitizenReportResponse:
    conv = conversation_manager.get_conversation(id)
    if not conv:
        conv = conversation_manager.create_conversation(id)

    p = conv.citizen_profile
    name_str = p.name or "नागरिक"
    age_str = f", उम्र {p.age} वर्ष" if p.age else ""
    gender_str = ", पुरुष" if p.gender == "Male" else (", महिला" if p.gender == "Female" else f", {p.gender}" if p.gender else "")
    loc_parts = [part for part in [p.district, p.state] if part]
    loc_str = f", निवासी {', '.join(loc_parts)}" if loc_parts else ""
    occ_str = f", पेशा: {p.occupation}" if p.occupation else ""
    
    inc_map = {
        "below_2_lakh": "वार्षिक आय ₹2,00,000 से कम",
        "2_to_5_lakh": "वार्षिक आय ₹2 लाख से ₹5 लाख के बीच",
        "above_5_lakh": "वार्षिक आय ₹5 लाख से अधिक"
    }
    inc_str = f", {inc_map.get(p.approx_income_bracket, '')}" if p.approx_income_bracket else ""

    selected_scheme_data = None
    if scheme_id is not None and conv.candidate_schemes:
        for s in conv.candidate_schemes:
            if s.get("id") == scheme_id:
                selected_scheme_data = s
                break

    if not selected_scheme_data and conv.candidate_schemes:
        selected_scheme_data = conv.candidate_schemes[0]

    scheme_mention = ""
    if selected_scheme_data:
        s_name = selected_scheme_data.get("name", "कल्याणकारी योजना")
        v = selected_scheme_data.get("verdict", "")
        v_str = "जिसके लिए आप पात्र हैं" if v == "QUALIFIES" else "जिसके लिए दस्तावेज़ सत्यापन अपेक्षित है"
        scheme_mention = f" आपकी चयनित योजना है: {s_name}, {v_str}।"

    docs_count = len(conv.collected_documents)
    docs_mention = f" कुल {docs_count} सरकारी दस्तावेज़ सत्यापित किए गए हैं।" if docs_count > 0 else " अभी कोई दस्तावेज़ स्कैन नहीं किया गया है।"

    report_text = f"नागरिक विवरण रिपोर्ट: {name_str}{age_str}{gender_str}{loc_str}{occ_str}{inc_str}।{docs_mention}{scheme_mention}"
    audio_b64 = _synthesize_audio_base64(report_text)

    return CitizenReportResponse(
        conversation_id=id,
        citizen_profile=p.model_dump(),
        stated_need=conv.stated_need,
        collected_documents=conv.collected_documents,
        recommended_schemes=conv.candidate_schemes,
        selected_scheme=selected_scheme_data,
        report_text_hindi=report_text,
        audio_base64=audio_b64,
        generated_at=datetime.now(timezone.utc).isoformat()
    )
