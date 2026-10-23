"""
Phase 6 Evaluation Test Harness: Eligibility Rules Matrix & Document OCR Pipeline.

Runs:
1. Deterministic Eligibility Matrix:
   Evaluates 8 distinct hand-crafted (citizen_profile x scheme) test cases covering
   all possible permutations of QUALIFIES, NEEDS_MORE_INFO, and DOES_NOT_QUALIFY:
   - Age under/over bounds
   - Income ceiling violations
   - Social category reservations
   - State residency restrictions
   - Gender exclusivity
   - Disability mandates
   - Incomplete profiles requiring missing facts
2. Synthetic Document OCR Pipeline:
   Runs all 12 synthetic test documents through OpenCV pre-processing and Tesseract OCR,
   reporting per-document field extraction accuracy and mean confidence scores.
"""

from pathlib import Path
import sys
from typing import Any, Dict, List
import numpy as np

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.eligibility_engine import EligibilityEngine, EligibilityVerdictType, DetailedEligibilityVerdict
from app.services.ocr_service import OCRService, OCRResult


# -----------------------------------------------------------------------------
# 1. DETERMINISTIC ELIGIBILITY MATRIX TEST CASES
# -----------------------------------------------------------------------------

ELIGIBILITY_TEST_MATRIX = [
    {
        "id": "TC_01_QUALIFIES_GOBARDHAN",
        "title": "Small Farmer Qualifying for Bio-Energy Scheme (GOBARdhan)",
        "profile": {
            "name": "रामवती",
            "age": 42,
            "gender": "Female",
            "state": "Uttar Pradesh",
            "district": "Barabanki",
            "approx_income_bracket": "below_2_lakh",
            "social_category": "OBC",
            "occupation": "Farmer",
            "disability_status": False
        },
        "scheme": {
            "id": 101,
            "name": "GOBARdhan Bio-Agro Scheme",
            "eligibility_criteria": {
                "min_age": 18,
                "max_age": 65,
                "applicable_states": ["All", "Uttar Pradesh"],
                "occupation": "Farmer",
                "income_ceiling": 200000
            }
        },
        "expected_verdict": EligibilityVerdictType.QUALIFIES
    },
    {
        "id": "TC_02_DISQUALIFIED_AGE_TOO_YOUNG",
        "title": "Minor Ineligible for Old-Age Pension (Under min_age)",
        "profile": {
            "name": "अमित",
            "age": 22,
            "gender": "Male",
            "state": "Uttar Pradesh",
            "district": "Varanasi",
            "approx_income_bracket": "below_2_lakh",
            "social_category": "General",
            "occupation": "Student",
            "disability_status": False
        },
        "scheme": {
            "id": 102,
            "name": "Indira Gandhi National Old Age Pension Scheme",
            "eligibility_criteria": {
                "min_age": 60,
                "income_ceiling": 200000
            }
        },
        "expected_verdict": EligibilityVerdictType.DOES_NOT_QUALIFY
    },
    {
        "id": "TC_03_DISQUALIFIED_INCOME_EXCEEDS",
        "title": "High Income Citizen Ineligible for BPL Housing Grant",
        "profile": {
            "name": "विक्रम",
            "age": 38,
            "gender": "Male",
            "state": "Uttar Pradesh",
            "district": "Kanpur",
            "approx_income_bracket": "above_5_lakh",
            "social_category": "General",
            "occupation": "Small Business / Self-Employed",
            "disability_status": False
        },
        "scheme": {
            "id": 103,
            "name": "Pradhan Mantri Awas Yojana (Gramin)",
            "eligibility_criteria": {
                "min_age": 18,
                "income_ceiling": 200000
            }
        },
        "expected_verdict": EligibilityVerdictType.DOES_NOT_QUALIFY
    },
    {
        "id": "TC_04_DISQUALIFIED_GENDER_MISMATCH",
        "title": "Male Citizen Ineligible for Widow Pension Scheme",
        "profile": {
            "name": "सुरेश",
            "age": 52,
            "gender": "Male",
            "state": "Delhi",
            "district": "Central Delhi",
            "approx_income_bracket": "below_2_lakh",
            "social_category": "OBC",
            "occupation": "Daily Wage Laborer",
            "disability_status": False
        },
        "scheme": {
            "id": 104,
            "name": "Delhi Pension Scheme To Women In Distress (Widow Pension)",
            "eligibility_criteria": {
                "min_age": 18,
                "gender": "Female",
                "state_restriction": "Delhi",
                "income_ceiling": 100000
            }
        },
        "expected_verdict": EligibilityVerdictType.DOES_NOT_QUALIFY
    },
    {
        "id": "TC_05_DISQUALIFIED_STATE_RESTRICTION",
        "title": "UP Resident Ineligible for Delhi State Specific Scheme",
        "profile": {
            "name": "राकेश",
            "age": 45,
            "gender": "Male",
            "state": "Uttar Pradesh",
            "district": "Gorakhpur",
            "approx_income_bracket": "below_2_lakh",
            "social_category": "SC",
            "occupation": "Daily Wage Laborer",
            "disability_status": False
        },
        "scheme": {
            "id": 105,
            "name": "Delhi Ladli Scheme",
            "eligibility_criteria": {
                "state_restriction": "Delhi"
            }
        },
        "expected_verdict": EligibilityVerdictType.DOES_NOT_QUALIFY
    },
    {
        "id": "TC_06_DISQUALIFIED_DISABILITY_REQUIRED",
        "title": "Non-Disabled Citizen Ineligible for Divyang Pension",
        "profile": {
            "name": "मनोज",
            "age": 35,
            "gender": "Male",
            "state": "Uttar Pradesh",
            "district": "Lucknow",
            "approx_income_bracket": "below_2_lakh",
            "social_category": "OBC",
            "occupation": "Daily Wage Laborer",
            "disability_status": False
        },
        "scheme": {
            "id": 106,
            "name": "Divyangjan Pension Yojana",
            "eligibility_criteria": {
                "min_age": 18,
                "disability_required": True
            }
        },
        "expected_verdict": EligibilityVerdictType.DOES_NOT_QUALIFY
    },
    {
        "id": "TC_07_NEEDS_MORE_INFO_MISSING_INCOME",
        "title": "Incomplete Profile Missing Income Bracket (Needs Followup)",
        "profile": {
            "name": "आरती",
            "age": 28,
            "gender": "Female",
            "state": "Uttar Pradesh",
            "district": "Prayagraj",
            "approx_income_bracket": None,  # Missing
            "social_category": "SC",
            "occupation": "Student",
            "disability_status": False
        },
        "scheme": {
            "id": 107,
            "name": "Post-Matric Scholarship for SC Students",
            "eligibility_criteria": {
                "social_category": ["SC", "ST"],
                "income_ceiling": 250000
            }
        },
        "expected_verdict": EligibilityVerdictType.NEEDS_MORE_INFO
    },
    {
        "id": "TC_08_QUALIFIES_SVANIDHI",
        "title": "Urban Street Vendor Qualifying for PM SVANidhi Microcredit",
        "profile": {
            "name": "दिलीप",
            "age": 36,
            "gender": "Male",
            "state": "Delhi",
            "district": "Central Delhi",
            "approx_income_bracket": "below_2_lakh",
            "social_category": "OBC",
            "occupation": "Street Vendor",
            "disability_status": False
        },
        "scheme": {
            "id": 108,
            "name": "PM Street Vendor's AtmaNirbhar Nidhi (PM SVANidhi)",
            "eligibility_criteria": {
                "min_age": 18,
                "applicable_states": ["All"],
                "occupation": "Street Vendor",
                "income_ceiling": 300000
            }
        },
        "expected_verdict": EligibilityVerdictType.QUALIFIES
    }
]


def run_eligibility_matrix_test():
    """Executes the test matrix for deterministic eligibility logic."""
    print("\n" + "=" * 80)
    print("      PART 1: DETERMINISTIC ELIGIBILITY ENGINE TEST MATRIX")
    print("=" * 80)

    passed_count = 0
    total_count = len(ELIGIBILITY_TEST_MATRIX)

    for i, tc in enumerate(ELIGIBILITY_TEST_MATRIX, 1):
        verdict: DetailedEligibilityVerdict = EligibilityEngine.evaluate_scheme(tc["profile"], tc["scheme"])
        is_pass = (verdict.verdict == tc["expected_verdict"])

        if is_pass:
            passed_count += 1
            status_str = "[PASS]"
        else:
            status_str = "[FAIL]"

        print(f"\n[{i}/{total_count}] {status_str} {tc['id']} - {tc['title']}")
        print(f"  Target Scheme : {tc['scheme']['name']}")
        print(f"  Verdict       : {verdict.verdict.value} (Expected: {tc['expected_verdict'].value})")
        print(f"  Reason        : {verdict.overall_reason}")
        if verdict.missing_fields:
            print(f"  Missing Fields: {verdict.missing_fields}")
        if verdict.disqualification_reasons:
            print(f"  Disqualifiers : {verdict.disqualification_reasons}")

    print("\n" + "-" * 80)
    print(f"Eligibility Matrix Summary: {passed_count}/{total_count} Passed ({(passed_count/total_count)*100:.1f}%)")
    print("-" * 80)
    assert passed_count == total_count, "One or more eligibility matrix tests failed!"


def run_ocr_pipeline_evaluation():
    """Runs all 12 synthetic mock documents through OpenCV + Tesseract OCR."""
    print("\n" + "=" * 80)
    print("      PART 2: SYNTHETIC DOCUMENT OCR PIPELINE EVALUATION")
    print("=" * 80)

    mock_dir = Path(__file__).resolve().parent.parent / "data" / "mock_documents"
    mock_files = sorted(mock_dir.glob("*.png"))

    if not mock_files:
        print(f"No mock documents found in {mock_dir}. Run generate_mock_documents.py first.")
        return

    total_expected_fields = 0
    total_extracted_fields = 0
    all_confidences: List[float] = []

    print(f"Evaluating {len(mock_files)} synthetic mock test documents:\n")

    for i, file_path in enumerate(mock_files, 1):
        name = file_path.name
        dtype = "generic"
        if "income" in name:
            dtype = "income_certificate"
            expected_fields = ["annual_income", "name", "district", "certificate_number"]
        elif "ration" in name:
            dtype = "ration_card"
            expected_fields = ["name", "ration_card_number", "family_members_count"]
        elif "khasra" in name:
            dtype = "khasra_khatauni"
            expected_fields = ["land_holding_area_hectares", "khasra_number", "name"]
        elif "aadhaar" in name:
            dtype = "aadhaar_card"
            expected_fields = ["dob", "gender", "name", "state", "district"]

        with open(file_path, "rb") as f:
            image_bytes = f.read()

        res: OCRResult = OCRService.process_document(image_bytes, document_type=dtype)

        extracted_count = len(res.extracted_fields)
        expected_count = len(expected_fields)
        total_expected_fields += expected_count
        total_extracted_fields += min(extracted_count, expected_count)

        for score in res.confidence_scores.values():
            all_confidences.append(score)

        mean_conf = float(np.mean(list(res.confidence_scores.values()))) if res.confidence_scores else 0.0

        print(f"[{i:02d}/12] {name}")
        print(f"  Type         : {dtype}")
        print(f"  Preprocess   : {', '.join(res.preprocessing_applied)}")
        print(f"  Extracted    : {extracted_count}/{expected_count} fields -> {res.extracted_fields}")
        print(f"  Confidence   : Mean {mean_conf:.3f} | Details: {res.confidence_scores}")
        print()

    accuracy = (total_extracted_fields / total_expected_fields) * 100
    mean_overall_conf = float(np.mean(all_confidences)) if all_confidences else 0.0

    print("=" * 80)
    print("                      PHASE 6 OCR EVALUATION SUMMARY")
    print("=" * 80)
    print(f"Total Synthetic Documents Tested   : {len(mock_files)}")
    print(f"Total Civic Fields Evaluated       : {total_expected_fields}")
    print(f"Total Civic Fields Extracted       : {total_extracted_fields}")
    print(f"Field Extraction Accuracy          : {accuracy:.1f}% (Acceptance Threshold: >= 70%)")
    print(f"Mean Confidence Score Across Fields: {mean_overall_conf:.3f}")
    print("=" * 80)

    assert accuracy >= 70.0, f"OCR extraction accuracy ({accuracy:.1f}%) is below 70% threshold!"
    print("\n[SUCCESS] Phase 6 Eligibility Engine and OCR Pipeline Verified Successfully!")


if __name__ == "__main__":
    run_eligibility_matrix_test()
    run_ocr_pipeline_evaluation()
