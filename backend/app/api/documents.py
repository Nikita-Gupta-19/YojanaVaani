"""
Document upload and OCR extraction API endpoints (Phase 6).

Provides:
- POST /documents/ocr: Accepts image file, executes OpenCV deskew & CLAHE pre-processing,
  runs Tesseract dual-language OCR, and extracts structured fields with confidence scores.
- POST /documents/confirm: Prepares extracted fields for yes/no confirmation step (ready for Phase 7 UI)
  and merges confirmed attributes into the active conversation's citizen profile.
"""

import logging
import uuid
from typing import Any, Dict, Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.services.ocr_service import OCRService, OCRResult
from app.services.conversation_manager import conversation_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

# In-memory document extraction cache for pending confirmations
_pending_documents: Dict[str, Dict[str, Any]] = {}


class DocumentConfirmRequest(BaseModel):
    """Payload to confirm or adjust fields extracted via OCR."""
    document_id: str = Field(..., description="Document identifier generated during /documents/ocr")
    conversation_id: Optional[str] = Field(default=None, description="Active conversation session ID to update")
    is_confirmed: bool = Field(default=True, description="Whether citizen verified extracted values")
    confirmed_fields: Dict[str, Any] = Field(default_factory=dict, description="Final confirmed fields (overrides if edited)")


class DocumentConfirmResponse(BaseModel):
    """Response confirming document fields ingestion into citizen profile."""
    status: str = Field(..., description="Status: 'confirmed', 'rejected', or 'updated'")
    document_id: str
    conversation_id: Optional[str]
    applied_profile_updates: Dict[str, Any]
    message: str


@router.post("/ocr", response_model=Dict[str, Any])
async def upload_and_process_document(
    file: UploadFile = File(..., description="Photograph or scan of citizen document"),
    document_type: str = Form("generic", description="Document type (income_certificate, ration_card, khasra_khatauni, aadhaar_card)"),
    conversation_id: Optional[str] = Form(None, description="Optional conversation ID to link with")
):
    """
    Accepts an uploaded document image, applies OpenCV deskew and contrast enhancement,
    and runs Tesseract OCR to extract domain-specific civic fields with confidence scores.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file has no filename.")

    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        ocr_result: OCRResult = OCRService.process_document(
            image_bytes=image_bytes,
            document_type=document_type
        )

        doc_id = f"doc_{uuid.uuid4().hex[:10]}"
        record = {
            "document_id": doc_id,
            "document_type": document_type,
            "conversation_id": conversation_id,
            "extracted_fields": ocr_result.extracted_fields,
            "confidence_scores": ocr_result.confidence_scores,
            "preprocessing_applied": ocr_result.preprocessing_applied,
            "raw_snippet": ocr_result.raw_ocr_text[:300]
        }
        _pending_documents[doc_id] = record

        # Generate a spoken vernacular confirmation prompt
        extracted_summary_parts = []
        for k, v in ocr_result.extracted_fields.items():
            if k == "annual_income":
                extracted_summary_parts.append(f"वार्षिक आय ₹{v:,.0f}")
            elif k == "name":
                extracted_summary_parts.append(f"नाम {v}")
            elif k == "land_holding_area_hectares":
                extracted_summary_parts.append(f"भूमि क्षेत्रफल {v} हेक्टेयर")
            elif k == "card_category":
                extracted_summary_parts.append(f"कार्ड प्रकार {v}")

        if extracted_summary_parts:
            confirm_prompt = f"दस्तावेज से प्राप्त जानकारी: {', '.join(extracted_summary_parts)}। क्या यह जानकारी सही है?"
        else:
            confirm_prompt = "दस्तावेज स्कैन हो चुका है। कृपया विवरण की पुष्टि करें।"

        return {
            "document_id": doc_id,
            "document_type": document_type,
            "extracted_fields": ocr_result.extracted_fields,
            "confidence_scores": ocr_result.confidence_scores,
            "preprocessing_applied": ocr_result.preprocessing_applied,
            "confirmation_prompt": confirm_prompt,
            "raw_ocr_snippet": ocr_result.raw_ocr_text[:300]
        }

    except Exception as e:
        logger.error(f"Error processing document upload: {e}")
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")


@router.post("/confirm", response_model=DocumentConfirmResponse)
async def confirm_document_fields(request: DocumentConfirmRequest):
    """
    Confirms OCR extracted fields, updating the citizen profile in the active conversation session.
    Ready for integration with Phase 7 React Native confirmation screen.
    """
    doc_record = _pending_documents.get(request.document_id)
    if not doc_record and not request.confirmed_fields:
        raise HTTPException(status_code=404, detail=f"Document ID '{request.document_id}' not found.")

    if not request.is_confirmed:
        return DocumentConfirmResponse(
            status="rejected",
            document_id=request.document_id,
            conversation_id=request.conversation_id,
            applied_profile_updates={},
            message="दस्तावेज विवरण अस्वीकृत कर दिया गया है। पुनः फोटो लें।"
        )

    # Use confirmed_fields if provided, otherwise fallback to OCR extracted fields
    final_fields = request.confirmed_fields or (doc_record.get("extracted_fields", {}) if doc_record else {})

    applied_updates: Dict[str, Any] = {}
    cid = request.conversation_id or (doc_record.get("conversation_id") if doc_record else None)

    if cid:
        session = conversation_manager.get_conversation(cid)
        if session:
            prof = session.citizen_profile

            if "name" in final_fields and final_fields["name"]:
                prof.name = str(final_fields["name"])
                applied_updates["name"] = prof.name

            if "annual_income" in final_fields:
                inc = float(final_fields["annual_income"])
                if inc < 200000:
                    prof.approx_income_bracket = "below_2_lakh"
                elif inc <= 500000:
                    prof.approx_income_bracket = "2_to_5_lakh"
                else:
                    prof.approx_income_bracket = "above_5_lakh"
                applied_updates["approx_income_bracket"] = prof.approx_income_bracket

            if "district" in final_fields and final_fields["district"]:
                prof.district = str(final_fields["district"])
                applied_updates["district"] = prof.district

            if "card_category" in final_fields:
                applied_updates["ration_card_category"] = final_fields["card_category"]

            if "land_holding_area_hectares" in final_fields:
                applied_updates["land_holding_area_hectares"] = final_fields["land_holding_area_hectares"]

            session.collected_documents.append({
                "document_id": request.document_id,
                "document_type": doc_record.get("document_type", "document") if doc_record else "document",
                "extracted_fields": final_fields
            })

    return DocumentConfirmResponse(
        status="confirmed",
        document_id=request.document_id,
        conversation_id=cid,
        applied_profile_updates=applied_updates,
        message="दस्तावेज विवरण सफलतापूर्वक सत्यापित व प्रोफाइल में जोड़ लिया गया है।"
    )
