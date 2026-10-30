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

import base64
import concurrent.futures
import json
import logging
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


class DocumentOCRResponse(BaseModel):
    """Response returned after running OpenCV + Tesseract OCR on an uploaded document."""
    conversation_id: str
    document_type: str
    extracted_fields: Dict[str, Any]
    confidence_scores: Dict[str, float]
    mean_confidence: float
    is_valid: bool
    raw_text: str


# -----------------------------------------------------------------------------
# HELPER: Audio Synthesis
# -----------------------------------------------------------------------------

_tts_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)


def _synthesize_audio_base64(text: str) -> Optional[str]:
    """Helper to synthesize Hindi text to base64 audio string via TTS provider with strict 2.0s timeout."""
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
        return future.result(timeout=2.0)
    except concurrent.futures.TimeoutError:
        logger.warning(f"TTS synthesis timed out after 2.0s for text: {text[:30]}...")
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
        audio_base64=audio_b64
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
                trans_result = asr.transcribe(audio_bytes=audio_bytes, language_code="hi")
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
                        trans_result = asr.transcribe(audio_bytes=audio_bytes, language_code="hi")
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
                audio_base64=audio_b64
            )
            return ConversationTurnResponse(
                conversation_id=conv.conversation_id,
                status=conv.status.value,
                transcribed_text=spoken_text,
                citizen_profile=conv.citizen_profile.model_dump(),
                action=action
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
        action=action
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
    file: UploadFile = File(..., description="Document photograph image file (PNG/JPG)"),
    document_type: Optional[str] = Form(None, description="Optional document type hint (income_certificate, ration_card, etc.)")
) -> DocumentOCRResponse:
    conv = conversation_manager.get_conversation(id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation ID '{id}' not found."
        )

    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No document image file uploaded."
        )

    image_bytes = await file.read()
    if not image_bytes or len(image_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded document file is empty."
        )

    result = OCRService.process_document(image_bytes=image_bytes, document_type=document_type or "generic")

    confs = list(result.confidence_scores.values())
    mean_conf = float(sum(confs) / len(confs)) if confs else 0.85
    is_valid = bool(len(result.extracted_fields) > 0 and mean_conf >= 0.70)

    return DocumentOCRResponse(
        conversation_id=id,
        document_type=result.document_type,
        extracted_fields=result.extracted_fields,
        confidence_scores=result.confidence_scores,
        mean_confidence=round(mean_conf, 3),
        is_valid=is_valid,
        raw_text=result.raw_ocr_text[:400]
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation ID '{id}' not found."
        )

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

        # Update Name if not already set or more formal
        if "name" in confirmed_fields and isinstance(confirmed_fields["name"], str):
            profile.name = confirmed_fields["name"].strip()

        # Update Location / State
        if "state" in confirmed_fields and isinstance(confirmed_fields["state"], str):
            profile.state = confirmed_fields["state"].strip()
        if "district" in confirmed_fields and isinstance(confirmed_fields["district"], str):
            profile.district = confirmed_fields["district"].strip()

        # Update Gender if present
        if "gender" in confirmed_fields and isinstance(confirmed_fields["gender"], str):
            profile.gender = confirmed_fields["gender"].strip()

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
