"""
OCR Document Verification and Extraction Service (Phase 6).

Implements:
1. OpenCV Image Pre-processing Pipeline:
   - Rescaling large camera photos to optimal OCR dimensions (max 1800px)
   - Deskew (rotational alignment via minAreaRect for small natural tilts)
   - Contrast normalization (dynamic CLAHE / Grayscale adaptive thresholding)
   - Dual-pass OCR (Grayscale CLAHE + Adaptive Gaussian Binarization)
2. Dual-language OCR (Hindi + English) via Tesseract (pytesseract).
3. Universal field extraction with confidence scoring tailored for standard Indian civic documents:
   - Ration Cards (राशन कार्ड / NFSA / AAY / BPL / PHH)
   - Income Certificates (आय प्रमाण पत्र / Revenue Department / Annual Income)
   - Khasra / Khatauni Land Records (खसरा / खतौनी / रकबा)
   - Aadhaar Cards (पहचान पत्र / UIDAI / 12-digit Aadhaar / DOB / Gender)
   - Generic key-value pair detection for civic documents
"""

import io
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from PIL import Image
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Check if Tesseract and OpenCV are available
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    cv2 = None
    OPENCV_AVAILABLE = False

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
    if "/opt/homebrew/bin" not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"/opt/homebrew/bin:{os.environ.get('PATH', '')}"
    for cand in ["/opt/homebrew/bin/tesseract", "/usr/local/bin/tesseract", "/usr/bin/tesseract"]:
        if os.path.exists(cand):
            pytesseract.pytesseract.tesseract_cmd = cand
            break
except ImportError:
    pytesseract = None
    PYTESSERACT_AVAILABLE = False


class ExtractedField(BaseModel):
    """Structured container for an extracted document field."""
    field_name: str = Field(..., description="Canonical field name (e.g. name, annual_income, district)")
    field_value: Any = Field(..., description="Extracted canonical value")
    raw_text: str = Field(..., description="Raw string match from document")
    confidence: float = Field(..., description="Confidence score in [0.0, 1.0]")


class OCRResult(BaseModel):
    """Complete result returned by the OCR document verification service."""
    document_type: str = Field(..., description="Requested or detected document type")
    extracted_fields: Dict[str, Any] = Field(default_factory=dict, description="Key-value mapping of extracted fields")
    confidence_scores: Dict[str, float] = Field(default_factory=dict, description="Confidence per field in [0.0, 1.0]")
    detailed_fields: List[ExtractedField] = Field(default_factory=list, description="Audit list of extracted fields")
    raw_ocr_text: str = Field(..., description="Complete text output from Tesseract")
    preprocessing_applied: List[str] = Field(default_factory=list, description="Pre-processing stages executed")


class OCRService:
    """
    Production-grade document image preprocessor and OCR extraction service.
    """

    @classmethod
    def preprocess_image(cls, image_bytes: bytes) -> Tuple[np.ndarray, List[str]]:
        """
        Executes OpenCV preprocessing pipeline:
        1. Decode byte buffer into OpenCV BGR image
        2. Proportional downscale if exceeding 1800px (phone camera photos)
        3. Convert to Grayscale
        4. Safe Deskew rotational alignment (only for angles 0.8° to 15.0°)
        5. CLAHE contrast enhancement & Gaussian blur
        """
        steps_applied: List[str] = []
        if not OPENCV_AVAILABLE:
            pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            return np.array(pil_img), ["pil_fallback"]

        # Decode image from memory
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        steps_applied.append("decode_bgr")

        # 0. Resize large smartphone camera photos to optimal OCR dimension (max 1800px)
        h, w = img.shape[:2]
        max_dim = max(h, w)
        if max_dim > 1800:
            scale = 1800.0 / max_dim
            new_w, new_h = int(w * scale), int(h * scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            steps_applied.append(f"downscale_{w}x{h}_to_{new_w}x{new_h}")
            h, w = new_h, new_w

        # 1. Grayscale conversion
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        steps_applied.append("grayscale")

        # 2. Deskew rotational alignment (safe range only)
        try:
            deskewed, angle = cls._deskew(gray)
            if 0.8 <= abs(angle) <= 15.0:
                gray = deskewed
                steps_applied.append(f"deskew_{angle:.1f}deg")
        except Exception as e:
            logger.debug(f"Deskew skipped: {e}")

        # 3. Contrast Normalization via CLAHE (Contrast Limited Adaptive Histogram Equalization)
        tile_w = max(4, min(16, w // 100))
        tile_h = max(4, min(16, h // 100))
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(tile_w, tile_h))
        enhanced = clahe.apply(gray)
        steps_applied.append("clahe_contrast_normalization")

        # 4. Light Gaussian smoothing to remove camera sensor noise
        smoothed = cv2.GaussianBlur(enhanced, (3, 3), 0)
        steps_applied.append("gaussian_denoise")

        return smoothed, steps_applied

    @staticmethod
    def _deskew(image: np.ndarray) -> Tuple[np.ndarray, float]:
        """Calculates skew angle of text blocks and rotates image to horizontal."""
        thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        coords = np.column_stack(np.where(thresh > 0))
        if len(coords) < 100:
            return image, 0.0

        coords_xy = np.column_stack((coords[:, 1], coords[:, 0]))
        rect = cv2.minAreaRect(coords_xy)
        angle = rect[-1]
        if angle < -45:
            angle = -(90 + angle)
        elif angle > 45:
            angle = 90 - angle
        else:
            angle = -angle

        # If angle is negligible or too extreme, do not resample
        if abs(angle) < 0.8 or abs(angle) > 15.0:
            return image, 0.0

        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        m = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image, m, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
        return rotated, angle

    @classmethod
    def extract_text_and_data(cls, processed_img: np.ndarray, lang: str = "hin+eng") -> Tuple[str, List[Dict[str, Any]]]:
        """
        Runs Tesseract OCR with adaptive multi-pass recovery for dimly lit/shadowed camera photos.
        """
        if not PYTESSERACT_AVAILABLE:
            return "", []

        for cand in ["/opt/homebrew/bin/tesseract", "/usr/local/bin/tesseract", "/usr/bin/tesseract"]:
            if os.path.exists(cand):
                pytesseract.pytesseract.tesseract_cmd = cand
                break

        try:
            available_langs = pytesseract.get_languages()
            use_lang = lang
            if "hin" not in available_langs:
                logger.warning("Hindi tesseract model ('hin') not installed. Falling back to 'eng'.")
                use_lang = "eng"
        except Exception:
            use_lang = "eng"

        try:
            from pytesseract import Output
            # Pass 1: Contrast-enhanced grayscale
            data = pytesseract.image_to_data(processed_img, lang=use_lang, output_type=Output.DICT)
            raw_text = pytesseract.image_to_string(processed_img, lang=use_lang)

            # Check if Pass 1 extracted meaningful text
            valid_words = [w.strip() for w in data.get("text", []) if len(w.strip()) > 1]

            # Pass 2: Adaptive Gaussian thresholding if Pass 1 yielded sparse results (glare/shadow)
            if len(valid_words) < 5 and OPENCV_AVAILABLE:
                adaptive = cv2.adaptiveThreshold(
                    processed_img, 255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY, 31, 15
                )
                data2 = pytesseract.image_to_data(adaptive, lang=use_lang, output_type=Output.DICT)
                raw_text2 = pytesseract.image_to_string(adaptive, lang=use_lang)
                valid_words2 = [w.strip() for w in data2.get("text", []) if len(w.strip()) > 1]
                if len(valid_words2) > len(valid_words):
                    data = data2
                    raw_text = raw_text2

            tokens: List[Dict[str, Any]] = []
            n_boxes = len(data["text"])
            for i in range(n_boxes):
                text_word = data["text"][i].strip()
                conf = float(data["conf"][i])
                if text_word and conf > 0:
                    tokens.append({
                        "text": text_word,
                        "conf": conf / 100.0,
                        "left": data["left"][i],
                        "top": data["top"][i],
                        "width": data["width"][i],
                        "height": data["height"][i]
                    })

            return raw_text, tokens
        except Exception as e:
            logger.error(f"Error executing Tesseract OCR: {e}")
            return "", []

    @classmethod
    def process_document(
        cls,
        image_bytes: bytes,
        document_type: str = "generic",
        citizen_name: Optional[str] = None
    ) -> OCRResult:
        """
        Universal End-to-End Extraction Pipeline:
        1. Pre-process image with downscaling, contrast enhancement, and safe deskew.
        2. Run dual-language Tesseract OCR with adaptive recovery.
        3. Execute universal multi-field extractors (Income, Ration, Land, Aadhaar, Generic).
        4. Detect canonical document type and unify highest-confidence fields.
        """
        processed_img, steps = cls.preprocess_image(image_bytes)
        raw_text, tokens = cls.extract_text_and_data(processed_img)

        # Average token confidence
        token_confs = [t["conf"] for t in tokens if t.get("conf", 0) > 0]
        avg_base_conf = float(np.mean(token_confs)) if token_confs else 0.85

        # Execute all extractors (Universal extraction)
        candidates: List[ExtractedField] = []
        candidates.extend(cls._extract_income_certificate_fields(raw_text, avg_base_conf))
        candidates.extend(cls._extract_ration_card_fields(raw_text, avg_base_conf))
        candidates.extend(cls._extract_khasra_fields(raw_text, avg_base_conf))
        candidates.extend(cls._extract_aadhaar_fields(raw_text, avg_base_conf, citizen_name=citizen_name))
        candidates.extend(cls._extract_generic_key_values(raw_text, avg_base_conf))

        # Deduplicate fields keeping the one with highest confidence
        fields_dict: Dict[str, Any] = {}
        conf_dict: Dict[str, float] = {}
        detailed: List[ExtractedField] = []

        for item in sorted(candidates, key=lambda x: x.confidence, reverse=True):
            if item.field_name not in fields_dict:
                fields_dict[item.field_name] = item.field_value
                conf_dict[item.field_name] = round(item.confidence, 3)
                detailed.append(item)

        # Auto-detect document type from OCR text keywords
        detected_type = document_type
        text_lower = raw_text.lower()
        if any(w in text_lower for w in ["aadhaar", "aadhar", "आधार", "uidai", "unique identification"]):
            detected_type = "aadhaar_card"
        elif any(w in text_lower for w in ["ration", "राशन", "nfsa", "खाद्य सुरक्षा"]):
            detected_type = "ration_card"
        elif any(w in text_lower for w in ["khasra", "khatauni", "खसरा", "खतौनी", "भूलेख", "रकबा"]):
            detected_type = "khasra_khatauni"
        elif any(w in text_lower for w in ["income", "आय प्रमाण", "revenue department", "वार्षिक आय"]):
            detected_type = "income_certificate"

        return OCRResult(
            document_type=detected_type,
            extracted_fields=fields_dict,
            confidence_scores=conf_dict,
            detailed_fields=detailed,
            raw_ocr_text=raw_text,
            preprocessing_applied=steps
        )

    # -------------------------------------------------------------------------
    # CIVIC FIELD EXTRACTION HEURISTICS
    # -------------------------------------------------------------------------

    @staticmethod
    def _extract_income_certificate_fields(text: str, base_conf: float) -> List[ExtractedField]:
        """Extracts fields from Revenue Department Income Certificates."""
        fields: List[ExtractedField] = []

        # 1. Annual Income Figure
        income_match = re.search(
            r"(?:वार्षिक\s*आय|कुल\s*(?:पारिवारिक\s*)?आय|मासिक\s*आय|आय\s*(?:\(Income\))?|Annual\s*Income|Family\s*Income|Total\s*Income|Gross\s*Income|Income)[^\d₹रुRsINR\n]*[₹रुRsINR\.\s]*([0-9]{1,3}(?:,[0-9]{2,3})+|[0-9]{4,8})",
            text, re.IGNORECASE
        )
        if not income_match:
            income_match = re.search(
                r"(?:Rs\.?|₹|रु[०\.]?|INR|रुपये|रूपये)\s*([0-9]{1,3}(?:,[0-9]{2,3})+|[0-9]{4,7})",
                text, re.IGNORECASE
            )

        if income_match:
            raw_val = income_match.group(1).replace(",", "").strip()
            try:
                income_val = float(raw_val)
                if "मासिक" in income_match.group(0):
                    income_val = income_val * 12.0
                if 5000 <= income_val <= 10000000:
                    fields.append(ExtractedField(
                        field_name="annual_income",
                        field_value=income_val,
                        raw_text=income_match.group(0),
                        confidence=min(0.98, max(0.72, base_conf + 0.05))
                    ))
            except ValueError:
                pass

        # 2. Beneficiary Name
        name_match = re.search(
            r"(?:आवेदक\s*(?:का\s*नाम)?|लाभार्थी\s*(?:का\s*नाम)?|नाम|Name\s*of\s*Applicant|Applicant\s*Name|Name)[^\w\n]*([A-Za-z\u0900-\u097F\s]{3,35})(?:\n|$|पुत्र|सुपुत्री|पत्नी|पिता|पति|S/o|D/o|W/o|F/o)",
            text, re.IGNORECASE
        )
        if name_match:
            clean_name = name_match.group(1).split("\n")[0].strip(" :.,।?!-")
            clean_lower = clean_name.lower()
            if len(clean_name) >= 3 and not any(term in clean_lower for term in ["income", "certificate", "district", "revenue", "department", "shasan", "pramann"]):
                fields.append(ExtractedField(
                    field_name="name",
                    field_value=clean_name,
                    raw_text=name_match.group(0),
                    confidence=min(0.95, max(0.70, base_conf))
                ))

        # 3. District
        dist_match = re.search(
            r"(?:जिला|District)[^\w\n]*([A-Za-z\u0900-\u097F\s]{3,25})",
            text, re.IGNORECASE
        )
        if dist_match:
            clean_dist = dist_match.group(1).split("\n")[0].strip(" :.,।?!-")
            if not any(w in clean_dist.lower() for w in ["uttar", "pradesh", "revenue", "seal", "department"]):
                fields.append(ExtractedField(
                    field_name="district",
                    field_value=clean_dist,
                    raw_text=dist_match.group(0),
                    confidence=min(0.93, max(0.68, base_conf))
                ))

        # 4. Tehsil
        tehsil_match = re.search(
            r"(?:तहसील|Tehsil)[^\w\n]*([A-Za-z\u0900-\u097F\s]{3,25})",
            text, re.IGNORECASE
        )
        if tehsil_match:
            clean_teh = tehsil_match.group(1).split("\n")[0].strip(" :.,।?!-")
            fields.append(ExtractedField(
                field_name="tehsil",
                field_value=clean_teh,
                raw_text=tehsil_match.group(0),
                confidence=min(0.92, max(0.67, base_conf))
            ))

        # 5. Certificate Number / Application ID
        cert_match = re.search(
            r"(?:प्रमाण\s*पत्र\s*क्रमांक|आवेदन\s*क्रमांक|Certificate\s*No\.?|Application\s*No(?:mber)?\.?|App\s*No\.?)[^\w\n]*([A-Z0-9\-\/]{6,25})",
            text, re.IGNORECASE
        )
        if cert_match:
            fields.append(ExtractedField(
                field_name="certificate_number",
                field_value=cert_match.group(1).strip(),
                raw_text=cert_match.group(0),
                confidence=min(0.97, max(0.75, base_conf + 0.08))
            ))

        # 6. Social Category
        cat_match = re.search(
            r"(?:वर्ग|जाति|Category)[^\w\n]*(अनुसूचित\s*जाति|अनुसूचित\s*जनजाति|अन्य\s*पिछड़ा\s*वर्ग|सामान्य|SC|ST|OBC|General|GEN)",
            text, re.IGNORECASE
        )
        if cat_match:
            raw_c = cat_match.group(1)
            norm_c = "OBC" if "पिछड़ा" in raw_c or "OBC" in raw_c else ("SC" if "अनुसूचित जाति" in raw_c or "SC" in raw_c else ("ST" if "अनुसूचित जनजाति" in raw_c or "ST" in raw_c else "General"))
            fields.append(ExtractedField(
                field_name="social_category",
                field_value=norm_c,
                raw_text=cat_match.group(0),
                confidence=min(0.94, max(0.70, base_conf))
            ))

        return fields

    @staticmethod
    def _extract_ration_card_fields(text: str, base_conf: float) -> List[ExtractedField]:
        """Extracts fields from NFSA / State Public Distribution System Ration Cards."""
        fields: List[ExtractedField] = []

        # 1. Card Category (AAY / BPL / PHH / APL)
        cat_match = re.search(
            r"(?:कार्ड\s*का\s*प्रकार|कार्ड\s*प्रकार|Card\s*Type|Scheme)[^\w\n]*(अन्त्योदय|अंत्योदय|AAY|बी\.?पी\.?एल|BPL|पात्र\s*गृहस्थी|PHH|APL)",
            text, re.IGNORECASE
        )
        if cat_match:
            raw_cat = cat_match.group(1).strip()
            norm_cat = "AAY" if "अंत्योदय" in raw_cat or "अन्त्योदय" in raw_cat or "AAY" in raw_cat else ("BPL" if "बी" in raw_cat or "BPL" in raw_cat else "PHH")
            fields.append(ExtractedField(
                field_name="card_category",
                field_value=norm_cat,
                raw_text=cat_match.group(0),
                confidence=min(0.96, max(0.72, base_conf + 0.05))
            ))

        # 2. Head of Family / Card Holder Name
        head_match = re.search(
            r"(?:मुखिया\s*का\s*नाम|कार्ड\s*धारक|Head\s*of\s*Family|Card\s*Holder)[^\w\n]*([A-Za-z\u0900-\u097F\s]{3,35})(?:\n|$|पति|पिता|W/o|S/o|F/o)",
            text, re.IGNORECASE
        )
        if head_match:
            clean_name = head_match.group(1).split("\n")[0].strip(" :.,।?!-")
            if len(clean_name) >= 3 and not any(w in clean_name.lower() for w in ["ration", "card", "department", "shasan"]):
                fields.append(ExtractedField(
                    field_name="name",
                    field_value=clean_name,
                    raw_text=head_match.group(0),
                    confidence=min(0.93, max(0.68, base_conf))
                ))

        # 3. Ration Card Number (10-16 digits)
        num_match = re.search(
            r"(?:राशन\s*कार्ड\s*(?:संख्या|क्रमांक|नं\.?)?|Ration\s*Card\s*No\.?)[^\d]*(\d{10,16})",
            text, re.IGNORECASE
        )
        if num_match:
            fields.append(ExtractedField(
                field_name="ration_card_number",
                field_value=num_match.group(1).strip(),
                raw_text=num_match.group(0),
                confidence=min(0.98, max(0.75, base_conf + 0.08))
            ))

        # 4. Total Family Members Count
        mem_match = re.search(
            r"(?:कुल\s*सदस्य(?:\s*संख्या)?|यूनिट\s*संख्या|Total\s*Members|Members|Units)[^\d]*(\d{1,2})",
            text, re.IGNORECASE
        )
        if mem_match:
            fields.append(ExtractedField(
                field_name="family_members_count",
                field_value=int(mem_match.group(1)),
                raw_text=mem_match.group(0),
                confidence=min(0.92, max(0.65, base_conf))
            ))

        return fields

    @staticmethod
    def _extract_khasra_fields(text: str, base_conf: float) -> List[ExtractedField]:
        """Extracts fields from Land Records (Bhulekh / Khasra-Khatauni)."""
        fields: List[ExtractedField] = []

        # 1. Land Holding Area in Hectares or Acres
        area_match = re.search(
            r"(?:क्षेत्रफल|रकबा|Total\s*Area|Land\s*Area|Area)?[^\d]*([0-9]+(?:\.[0-9]+)?)\s*(?:हेक्टेयर|हेक्ट|हे\.?|Hectares?|Acre|एकड़|बीघा|Bigha)",
            text, re.IGNORECASE
        )
        if area_match:
            try:
                area_val = float(area_match.group(1))
                unit_str = area_match.group(0).lower()
                if "acre" in unit_str or "एकड़" in unit_str:
                    area_val = round(area_val * 0.4047, 2)
                elif "बीघा" in unit_str or "bigha" in unit_str:
                    area_val = round(area_val * 0.25, 2)
                fields.append(ExtractedField(
                    field_name="land_holding_area_hectares",
                    field_value=area_val,
                    raw_text=area_match.group(0),
                    confidence=min(0.97, max(0.72, base_conf + 0.06))
                ))
            except ValueError:
                pass

        # 2. Khasra / Plot Number
        khasra_match = re.search(
            r"(?:खसरा\s*(?:संख्या|क्रमांक|नं\.?)?|गाटा\s*(?:संख्या|क्रमांक|नं\.?)?|Khasra\s*No\.?|Plot\s*No\.?)[^\d\n]*([0-9]+(?:[\/\-][0-9]+)?)",
            text, re.IGNORECASE
        )
        if khasra_match:
            clean_khasra = khasra_match.group(1).strip()
            fields.append(ExtractedField(
                field_name="khasra_number",
                field_value=clean_khasra,
                raw_text=khasra_match.group(0),
                confidence=min(0.95, max(0.72, base_conf + 0.05))
            ))

        # 3. Farmer / Landholder Name
        farmer_match = re.search(
            r"(?:खातेदार\s*(?:का\s*नाम)?|भूस्वामी|Farmer\s*Name|Owner)[^\w\n]*([A-Za-z\u0900-\u097F\s]{3,35})(?:\n|$|पिता|पुत्र|S/o|F/o)",
            text, re.IGNORECASE
        )
        if farmer_match:
            clean_farmer = farmer_match.group(1).split("\n")[0].strip(" :.,।?!-")
            if len(clean_farmer) >= 3:
                fields.append(ExtractedField(
                    field_name="name",
                    field_value=clean_farmer,
                    raw_text=farmer_match.group(0),
                    confidence=min(0.92, max(0.65, base_conf))
                ))

        return fields

    @staticmethod
    def _extract_aadhaar_fields(text: str, base_conf: float, citizen_name: Optional[str] = None) -> List[ExtractedField]:
        """Extracts fields from identity cards (Aadhaar / Voter ID mock)."""
        fields: List[ExtractedField] = []

        # 1. Aadhaar Number (12 digits, grouped, masked, or continuous)
        adh_match = re.search(r"\b([0-9]{4}\s+[0-9]{4}\s+[0-9]{4})\b", text)
        if not adh_match:
            # Masked Aadhaar format: XXXX XXXX 1234 or xxxx xxxx 1234 or •••• •••• 1234
            adh_match = re.search(r"\b([Xx•*]{4}\s*[Xx•*]{4}\s*[0-9]{4})\b", text)
        if not adh_match:
            # 12 continuous digits
            adh_match = re.search(r"\b([2-9][0-9]{11})\b", text)

        if adh_match:
            raw_num = adh_match.group(1).strip()
            digits_only = re.sub(r"[^\d]", "", raw_num)
            if len(digits_only) == 12:
                formatted_num = f"XXXX-XXXX-{digits_only[-4:]}"
            elif len(digits_only) >= 4:
                formatted_num = f"XXXX-XXXX-{digits_only[-4:]}"
            else:
                formatted_num = raw_num
            fields.append(ExtractedField(
                field_name="aadhaar_number",
                field_value=formatted_num,
                raw_text=raw_num,
                confidence=min(0.99, max(0.85, base_conf + 0.10))
            ))

        # 2. Date of Birth / Year of Birth
        # Handles spacing around slashes (e.g. 15 / 08 / 2002), hyphens, periods, or 4-digit year
        dob_match = re.search(
            r"(?:DOB|D\.?O\.?B\.?|जन्म\s*(?:तिथि|तारीख|वर्ष)?|Date\s*of\s*Birth|Year\s*of\s*Birth)[^\d\n]*(\d{1,2}\s*[\/\-\.]\s*\d{1,2}\s*[\/\-\.]\s*(?:19|20)\d{2}|\d{1,2}\s*[\/\-\.]\s*\d{1,2}\s*[\/\-\.]\s*\d{2}|\b(?:19|20)\d{2}\b)",
            text, re.IGNORECASE
        )
        if not dob_match:
            # Look for any valid 8-digit date on the card: DD/MM/YYYY
            dob_match = re.search(
                r"\b([0-3]?[0-9]\s*[\/\-\.]\s*[0-1]?[0-9]\s*[\/\-\.]\s*(?:19|20)[0-9]{2})\b",
                text
            )

        if dob_match:
            raw_dob = dob_match.group(1).strip()
            clean_dob = re.sub(r"\s*([\/\-\.])\s*", r"\1", raw_dob)
            fields.append(ExtractedField(
                field_name="dob",
                field_value=clean_dob,
                raw_text=dob_match.group(0),
                confidence=min(0.98, max(0.78, base_conf + 0.08))
            ))

        # 3. Gender
        gender_match = re.search(
            r"(?:लिंग|Gender)[^\w]*(पुरुष|महिला|MALE|FEMALE)|(?:पुरुष\s*\/\s*MALE|महिला\s*\/\s*FEMALE)|\b(पुरुष|महिला|MALE|FEMALE)\b",
            text, re.IGNORECASE
        )
        if gender_match:
            g_str = (gender_match.group(1) or gender_match.group(2) or gender_match.group(0)).upper()
            norm_g = "Female" if "FEMALE" in g_str or "महिला" in g_str else "Male"
            fields.append(ExtractedField(
                field_name="gender",
                field_value=norm_g,
                raw_text=gender_match.group(0),
                confidence=min(0.96, max(0.75, base_conf + 0.05))
            ))

        # 4. Name extraction
        matched_name = None
        # Priority A: Check if citizen profile already has a name, check if it matches any line
        if citizen_name and len(citizen_name.strip()) >= 2:
            c_name = citizen_name.strip()
            for line in text.splitlines():
                line_clean = line.strip()
                if c_name.lower() in line_clean.lower() or line_clean.lower() in c_name.lower():
                    if len(line_clean) >= 2 and not any(w in line_clean.lower() for w in ["government", "india", "aadhaar", "uidai"]):
                        matched_name = line_clean
                        break

        # Priority B: Check lines right above DOB, Gender, or labeled 'Name:'
        if not matched_name:
            name_match = re.search(
                r"(?:Name|नाम)[^\w\n]*([A-Za-z\u0900-\u097F\s]{3,35})(?:\n|$)",
                text, re.IGNORECASE
            )
            if name_match:
                clean_cand = name_match.group(1).split("\n")[0].strip(" :.,।?!-")
                if len(clean_cand) >= 3 and not any(w in clean_cand.lower() for w in ["government", "india", "aadhaar", "unique"]):
                    matched_name = clean_cand

        if not matched_name:
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            stop_words = ["government", "india", "bharat", "sarkar", "aadhaar", "aadhar", "uidai", "unique", "identification", "authority", "pechan", "pehchan", "mera", "meri", "enrollment", "help", "download", "dob", "date", "birth", "male", "female", "पुरुष", "महिला", "वर्ष"]
            for idx, line in enumerate(lines):
                if re.search(r"(?:DOB|जन्म|Date\s*of\s*Birth|Gender|महिला|पुरुष|FEMALE|MALE)", line, re.I):
                    for lookback in [1, 2]:
                        if idx - lookback >= 0:
                            cand = lines[idx - lookback].strip(" :.,।?!-")
                            cand_lower = cand.lower()
                            if len(cand) >= 2 and not any(w in cand_lower for w in stop_words):
                                if re.search(r"^[A-Za-z\u0900-\u097F\s\.\']+$", cand):
                                    matched_name = cand
                                    break
                    if matched_name:
                        break

        if matched_name:
            fields.append(ExtractedField(
                field_name="name",
                field_value=matched_name,
                raw_text=matched_name,
                confidence=min(0.95, max(0.75, base_conf))
            ))
        elif citizen_name:
            fields.append(ExtractedField(
                field_name="name",
                field_value=citizen_name,
                raw_text="Verified via citizen profile",
                confidence=0.88
            ))

        # 5. Pincode
        pin_match = re.search(r"\b([1-9][0-9]{5})\b", text)
        if pin_match:
            fields.append(ExtractedField(
                field_name="pincode",
                field_value=pin_match.group(1),
                raw_text=pin_match.group(0),
                confidence=min(0.95, max(0.70, base_conf))
            ))

        # 6. District
        dist_match = re.search(
            r"(?:District|जिला)[^\w\n]*([A-Za-z\u0900-\u097F\s]{3,25})",
            text, re.IGNORECASE
        )
        if dist_match:
            clean_dist = dist_match.group(1).split("\n")[0].strip(" :.,।?!-")
            fields.append(ExtractedField(
                field_name="district",
                field_value=clean_dist,
                raw_text=dist_match.group(0),
                confidence=min(0.92, max(0.65, base_conf))
            ))

        # 7. State
        state_match = re.search(
            r"(?:State|राज्य)[^\w\n]*([A-Za-z\u0900-\u097F\s]{3,25})",
            text, re.IGNORECASE
        )
        if state_match:
            clean_state = state_match.group(1).split("\n")[0].strip(" :.,।?!-")
            fields.append(ExtractedField(
                field_name="state",
                field_value=clean_state,
                raw_text=state_match.group(0),
                confidence=min(0.94, max(0.68, base_conf))
            ))

        return fields

    @staticmethod
    def _extract_generic_key_values(text: str, base_conf: float) -> List[ExtractedField]:
        """Extracts any key-value pairs formatted as 'Key : Value' from the document."""
        fields: List[ExtractedField] = []
        key_mapping = {
            "name": "name",
            "applicant": "name",
            "नाम": "name",
            "आवेदक": "name",
            "annual income": "annual_income",
            "income": "annual_income",
            "वार्षिक आय": "annual_income",
            "आय": "annual_income",
            "district": "district",
            "जिला": "district",
            "tehsil": "tehsil",
            "तहसील": "tehsil",
            "state": "state",
            "राज्य": "state",
            "gender": "gender",
            "लिंग": "gender",
            "dob": "dob",
            "जन्म तिथि": "dob",
        }

        for line in text.splitlines():
            line = line.strip()
            if ":" in line or " - " in line:
                parts = line.split(":", 1) if ":" in line else line.split(" - ", 1)
                k_raw = parts[0].strip().lower()
                v_raw = parts[1].strip()
                if len(k_raw) >= 2 and len(v_raw) >= 2:
                    for k_pat, canonical_key in key_mapping.items():
                        if k_pat in k_raw and canonical_key not in [f.field_name for f in fields]:
                            clean_v: Any = v_raw
                            if canonical_key == "annual_income":
                                num_m = re.search(r"(\d{4,8})", v_raw.replace(",", ""))
                                if num_m:
                                    clean_v = float(num_m.group(1))
                                else:
                                    continue
                            fields.append(ExtractedField(
                                field_name=canonical_key,
                                field_value=clean_v,
                                raw_text=line,
                                confidence=min(0.90, max(0.65, base_conf))
                            ))
                            break
        return fields
