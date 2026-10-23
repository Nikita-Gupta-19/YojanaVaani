"""
OCR Document Verification and Extraction Service (Phase 6).

Implements:
1. OpenCV Image Pre-processing Pipeline:
   - Deskew (rotational alignment via minAreaRect)
   - Contrast normalization (CLAHE / Grayscale adaptive thresholding)
   - Noise filtering & edge preservation
2. Dual-language OCR (Hindi + English) via Tesseract (pytesseract).
3. Field extraction with confidence scoring tailored for standard Indian civic documents:
   - Ration Cards (राशन कार्ड)
   - Income Certificates (आय प्रमाण पत्र)
   - Khasra / Khatauni Land Records (खसरा / खतौनी)
   - Aadhaar Mock Cards (पहचान पत्र)
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
        2. Convert to Grayscale
        3. Deskew rotation
        4. CLAHE contrast enhancement & Gaussian blur
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

        # 1. Grayscale conversion
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        steps_applied.append("grayscale")

        # 2. Deskew rotational alignment
        try:
            deskewed, angle = cls._deskew(gray)
            if abs(angle) > 0.3:
                gray = deskewed
                steps_applied.append(f"deskew_{angle:.1f}deg")
        except Exception as e:
            logger.debug(f"Deskew skipped: {e}")

        # 3. Contrast Normalization via CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        steps_applied.append("clahe_contrast_normalization")

        # 4. Light Gaussian smoothing to remove scan artifacts
        smoothed = cv2.GaussianBlur(enhanced, (3, 3), 0)
        steps_applied.append("gaussian_denoise")

        return smoothed, steps_applied

    @staticmethod
    def _deskew(image: np.ndarray) -> Tuple[np.ndarray, float]:
        """Calculates skew angle of text blocks and rotates image to horizontal."""
        # Invert colors for bounding box calculation: text as foreground (white)
        thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

        coords = np.column_stack(np.where(thresh > 0))
        if len(coords) < 50:
            return image, 0.0

        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        # If angle is negligible, do not resample
        if abs(angle) < 0.5 or abs(angle) > 45.0:
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
        Runs Tesseract OCR extracting both raw text and per-token bounding boxes / confidences.
        """
        if not PYTESSERACT_AVAILABLE:
            return "", []

        # Find tesseract binary if not in default PATH
        for cand in ["/opt/homebrew/bin/tesseract", "/usr/local/bin/tesseract", "/usr/bin/tesseract"]:
            if os.path.exists(cand):
                pytesseract.pytesseract.tesseract_cmd = cand
                break

        # Check supported languages
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
            data = pytesseract.image_to_data(processed_img, lang=use_lang, output_type=Output.DICT)
            raw_text = pytesseract.image_to_string(processed_img, lang=use_lang)

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
    def process_document(cls, image_bytes: bytes, document_type: str = "generic") -> OCRResult:
        """
        End-to-end pipeline:
        1. Pre-process image with OpenCV.
        2. Run dual-language Tesseract OCR.
        3. Parse structured civic fields using domain-specific heuristics.
        """
        processed_img, steps = cls.preprocess_image(image_bytes)
        raw_text, tokens = cls.extract_text_and_data(processed_img)

        # Average token confidence
        token_confs = [t["conf"] for t in tokens if t.get("conf", 0) > 0]
        avg_base_conf = float(np.mean(token_confs)) if token_confs else 0.85

        doc_lower = document_type.lower()
        extracted: List[ExtractedField] = []

        if "income" in doc_lower:
            extracted = cls._extract_income_certificate_fields(raw_text, avg_base_conf)
        elif "ration" in doc_lower:
            extracted = cls._extract_ration_card_fields(raw_text, avg_base_conf)
        elif "khasra" in doc_lower or "khatauni" in doc_lower or "land" in doc_lower:
            extracted = cls._extract_khasra_fields(raw_text, avg_base_conf)
        elif "aadhaar" in doc_lower or "identity" in doc_lower:
            extracted = cls._extract_aadhaar_fields(raw_text, avg_base_conf)
        else:
            # Try all extractors and pick best match
            extracted = (
                cls._extract_income_certificate_fields(raw_text, avg_base_conf)
                or cls._extract_ration_card_fields(raw_text, avg_base_conf)
                or cls._extract_khasra_fields(raw_text, avg_base_conf)
                or cls._extract_aadhaar_fields(raw_text, avg_base_conf)
            )

        fields_dict: Dict[str, Any] = {}
        conf_dict: Dict[str, float] = {}

        for item in extracted:
            fields_dict[item.field_name] = item.field_value
            conf_dict[item.field_name] = round(item.confidence, 3)

        return OCRResult(
            document_type=document_type,
            extracted_fields=fields_dict,
            confidence_scores=conf_dict,
            detailed_fields=extracted,
            raw_ocr_text=raw_text,
            preprocessing_applied=steps
        )

    # -------------------------------------------------------------------------
    # CIVIC FIELD EXTRACTION HEURISTICS
    # -------------------------------------------------------------------------

    @staticmethod
    def _extract_income_certificate_fields(text: str, base_conf: float) -> List[ExtractedField]:
        """Extracts fields from standard Revenue Department Income Certificates."""
        fields: List[ExtractedField] = []

        # 1. Annual Income Figure (e.g. ₹60,000 / 60000 / रु. 48,000 / Rs. 48000)
        income_match = re.search(
            r"(?:वार्षिक\s*आय|कुल\s*आय|Annual\s*Income|Total\s*Income)[^\d₹रुRs]*[₹रुRs\.\s]*(\d{4,8}|\d{1,3}(?:,\d{2,3})*(?:\.\d{2})?)",
            text, re.IGNORECASE
        )
        if income_match:
            raw_val = income_match.group(1).replace(",", "").strip()
            try:
                income_val = float(raw_val)
                fields.append(ExtractedField(
                    field_name="annual_income",
                    field_value=income_val,
                    raw_text=income_match.group(0),
                    confidence=min(0.98, max(0.70, base_conf + 0.05))
                ))
            except ValueError:
                pass

        # 2. Beneficiary Name
        name_match = re.search(
            r"(?:नाम|प्रमाणित\s*किया\s*जाता\s*है\s*कि|Name\s*of\s*Applicant|Shri|Smt)[^\w\n]*([A-Za-z\u0900-\u097F\s]{3,35})(?:\n|पुत्र|सुपुत्री|पत्नी|S/o|D/o|W/o)",
            text, re.IGNORECASE
        )
        if name_match:
            clean_name = name_match.group(1).split("\n")[0].strip(" :.,।?!")
            if len(clean_name) >= 3 and not any(term in clean_name.lower() for term in ["income", "certificate", "district"]):
                fields.append(ExtractedField(
                    field_name="name",
                    field_value=clean_name,
                    raw_text=name_match.group(0),
                    confidence=min(0.95, max(0.68, base_conf))
                ))

        # 3. District / State
        dist_match = re.search(
            r"(?:जिला|District)[^\w\n]*([A-Za-z\u0900-\u097F\s]{3,25})",
            text, re.IGNORECASE
        )
        if dist_match:
            clean_dist = dist_match.group(1).split("\n")[0].strip(" :.,।?!")
            fields.append(ExtractedField(
                field_name="district",
                field_value=clean_dist,
                raw_text=dist_match.group(0),
                confidence=min(0.92, max(0.65, base_conf))
            ))

        # 4. Certificate Number / Application ID
        cert_match = re.search(
            r"(?:प्रमाण\s*पत्र\s*क्रमांक|आवेदन\s*क्रमांक|Certificate\s*No|Application\s*No)[^\w\n]*([A-Z0-9\-\/]{6,25})",
            text, re.IGNORECASE
        )
        if cert_match:
            fields.append(ExtractedField(
                field_name="certificate_number",
                field_value=cert_match.group(1).strip(),
                raw_text=cert_match.group(0),
                confidence=min(0.97, max(0.75, base_conf + 0.08))
            ))

        return fields

    @staticmethod
    def _extract_ration_card_fields(text: str, base_conf: float) -> List[ExtractedField]:
        """Extracts fields from NFSA / State Public Distribution System Ration Cards."""
        fields: List[ExtractedField] = []

        # 1. Card Category (AAY / BPL / PHH / APL)
        cat_match = re.search(
            r"(?:कार्ड\s*का\s*प्रकार|Card\s*Type|Scheme)[^\w\n]*(अंत्योदय|AAY|बी\.?पी\.?एल|BPL|पात्र\s*गृहस्थी|PHH|APL)",
            text, re.IGNORECASE
        )
        if cat_match:
            raw_cat = cat_match.group(1).strip()
            norm_cat = "AAY" if "अंत्योदय" in raw_cat or "AAY" in raw_cat else ("BPL" if "बी" in raw_cat or "BPL" in raw_cat else "PHH")
            fields.append(ExtractedField(
                field_name="card_category",
                field_value=norm_cat,
                raw_text=cat_match.group(0),
                confidence=min(0.96, max(0.72, base_conf + 0.05))
            ))

        # 2. Head of Family / Card Holder Name
        head_match = re.search(
            r"(?:मुखिया\s*का\s*नाम|कार्ड\s*धारक|Head\s*of\s*Family)[^\w\n]*([A-Za-z\u0900-\u097F\s]{3,35})(?:\n|पति|पिता|W/o|S/o)",
            text, re.IGNORECASE
        )
        if head_match:
            clean_name = head_match.group(1).split("\n")[0].strip(" :.,।?!")
            fields.append(ExtractedField(
                field_name="name",
                field_value=clean_name,
                raw_text=head_match.group(0),
                confidence=min(0.93, max(0.68, base_conf))
            ))

        # 3. Ration Card Number (usually 10-14 digits)
        num_match = re.search(
            r"(?:राशन\s*कार्ड\s*संख्या|Ration\s*Card\s*No)[^\d]*(\d{10,16})",
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
            r"(?:कुल\s*सदस्य|यूनिट\s*संख्या|Total\s*Members|Units)[^\d]*(\d{1,2})",
            text, re.IGNORECASE
        )
        if mem_match:
            fields.append(ExtractedField(
                field_name="family_members_count",
                field_value=int(mem_match.group(1)),
                raw_text=mem_match.group(0),
                confidence=min(0.91, max(0.62, base_conf))
            ))

        return fields

    @staticmethod
    def _extract_khasra_fields(text: str, base_conf: float) -> List[ExtractedField]:
        """Extracts fields from Land Records (Bhulekh / Khasra-Khatauni)."""
        fields: List[ExtractedField] = []

        # 1. Land Holding Area in Hectares or Acres (e.g. 0.84 Hectares / 1.65 Hectares)
        area_match = re.search(
            r"(?:क्षेत्रफल|रकबा|Total\s*Area|Land\s*Area|Area)?[^\d]*(\d+(?:\.\d+)?)\s*(?:हेक्टेयर|हेक्ट|हे\.?|Hectares?|Acre|एकड़)",
            text, re.IGNORECASE
        )
        if area_match:
            try:
                area_val = float(area_match.group(1))
                fields.append(ExtractedField(
                    field_name="land_holding_area_hectares",
                    field_value=area_val,
                    raw_text=area_match.group(0),
                    confidence=min(0.97, max(0.72, base_conf + 0.06))
                ))
            except ValueError:
                pass

        # 2. Khasra / Plot Number (e.g. खसरा संख्या 142/1 or Plot No 142/2)
        khasra_match = re.search(
            r"(?:खसरा\s*संख्या|गाटा\s*संख्या|Khasra\s*No|Plot\s*No)[^\w\n]*([\w\/\-\s,]{1,25})",
            text, re.IGNORECASE
        )
        if khasra_match:
            clean_khasra = khasra_match.group(1).split("\n")[0].strip(" :.,।?!")
            fields.append(ExtractedField(
                field_name="khasra_number",
                field_value=clean_khasra,
                raw_text=khasra_match.group(0),
                confidence=min(0.94, max(0.70, base_conf + 0.05))
            ))

        # 3. Landholder / Farmer Name
        farmer_match = re.search(
            r"(?:खातेदार\s*का\s*नाम|भूस्वामी|Farmer\s*Name|Owner)[^\w\n]*([A-Za-z\u0900-\u097F\s]{3,35})(?:\n|पिता|पुत्र|S/o)",
            text, re.IGNORECASE
        )
        if farmer_match:
            clean_farmer = farmer_match.group(1).split("\n")[0].strip(" :.,।?!")
            fields.append(ExtractedField(
                field_name="name",
                field_value=clean_farmer,
                raw_text=farmer_match.group(0),
                confidence=min(0.92, max(0.65, base_conf))
            ))

        return fields

    @staticmethod
    def _extract_aadhaar_fields(text: str, base_conf: float) -> List[ExtractedField]:
        """Extracts fields from identity cards (Aadhaar / Voter ID mock)."""
        fields: List[ExtractedField] = []

        # 1. Date of Birth / Year of Birth
        dob_match = re.search(
            r"(?:DOB|जन्म\s*तिथि|Year\s*of\s*Birth|जन्म\s*वर्ष)[^\d]*([\d\/\-]{4,12})",
            text, re.IGNORECASE
        )
        if dob_match:
            fields.append(ExtractedField(
                field_name="dob",
                field_value=dob_match.group(1).strip(" :.,।?!"),
                raw_text=dob_match.group(0),
                confidence=min(0.98, max(0.75, base_conf + 0.08))
            ))

        # 2. Gender
        gender_match = re.search(
            r"(?:महिला|FEMALE|पुरुष|MALE|Transgender)",
            text, re.IGNORECASE
        )
        if gender_match:
            g_str = gender_match.group(0).upper()
            norm_g = "Female" if "FEMALE" in g_str or "महिला" in g_str else "Male"
            fields.append(ExtractedField(
                field_name="gender",
                field_value=norm_g,
                raw_text=gender_match.group(0),
                confidence=min(0.95, max(0.70, base_conf + 0.05))
            ))

        # 3. Full Name
        name_match = re.search(
            r"(?:Name|नाम)[^\w\n]*([A-Za-z\u0900-\u097F\s]{3,35})",
            text, re.IGNORECASE
        )
        if name_match:
            clean_name = name_match.group(1).split("\n")[0].strip(" :.,।?!")
            fields.append(ExtractedField(
                field_name="name",
                field_value=clean_name,
                raw_text=name_match.group(0),
                confidence=min(0.93, max(0.67, base_conf))
            ))

        # 4. State
        state_match = re.search(
            r"(?:State|राज्य)[^\w\n]*([A-Za-z\u0900-\u097F\s]{3,25})",
            text, re.IGNORECASE
        )
        if state_match:
            clean_state = state_match.group(1).split("\n")[0].strip(" :.,।?!")
            fields.append(ExtractedField(
                field_name="state",
                field_value=clean_state,
                raw_text=state_match.group(0),
                confidence=min(0.94, max(0.68, base_conf))
            ))

        # 5. District
        dist_match = re.search(
            r"(?:District|जिला)[^\w\n]*([A-Za-z\u0900-\u097F\s]{3,25})",
            text, re.IGNORECASE
        )
        if dist_match:
            clean_dist = dist_match.group(1).split("\n")[0].strip(" :.,।?!")
            fields.append(ExtractedField(
                field_name="district",
                field_value=clean_dist,
                raw_text=dist_match.group(0),
                confidence=min(0.92, max(0.65, base_conf))
            ))

        return fields

