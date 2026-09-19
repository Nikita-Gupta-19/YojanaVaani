"""
Fine-print conditions extraction for YojanaVaani Phase 2.

Captures all additional terms, conditions, restrictions, and fine print:
- exclusion (disqualifying attributes, e.g. bank defaulter, government employee, income tax payer)
- documentation (required certificates, land records, ration cards, licenses)
- procedural (mandatory processes, e.g. margin money, physical verification, biometric check)
- combination_restriction (overlap with other government pensions or subsidies)
- quota (household/family limits, e.g. one member per family, maximum two surviving children)

Retains original official wording wherever practical and marks verifiable_from_profile.
"""

import json
import logging
import os
import re
import sys
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "scraped_schemes.json")


class FinePrintCondition(BaseModel):
    text: str = Field(description="Clear, concise description of the fine-print rule or condition")
    category: Literal["exclusion", "documentation", "procedural", "combination_restriction", "quota"] = Field(
        description="Category: exclusion, documentation, procedural, combination_restriction, or quota"
    )
    verifiable_from_profile: bool = Field(
        description="True if verifiable directly from standard user profile, False if requires external check or specific document."
    )


def extract_scheme_fine_print(scheme: dict) -> List[dict]:
    """Extracts fine-print conditions directly from official conditions, benefits, and process text."""
    conditions = []
    seen_texts = set()

    elig = scheme.get("eligibility_criteria", {})
    other_cond = elig.get("other_conditions_text", "")
    benefits = scheme.get("benefits", "")
    app_proc = scheme.get("application_process", "")

    full_text = f"{other_cond}\n{benefits}\n{app_proc}"
    lines = [line.strip("- *1234567890.) \t") for line in full_text.split("\n") if len(line.strip()) > 20]

    for line in lines:
        lower = line.lower()
        cat = None
        verifiable = False

        # 1. Quota
        if any(k in lower for k in [
            "one member per", "one person per", "per family", "per household", "only one beneficiary",
            "maximum of two", "two surviving children", "two children", "limit of two", "single unit"
        ]):
            cat = "quota"
            verifiable = False

        # 2. Combination restriction
        elif any(k in lower for k in [
            "already availed", "availed subsidy", "not have availed", "under any other scheme",
            "under cmss", "under pmegp", "dual benefit", "another pension", "similar benefit",
            "overlapping scheme", "not receiving any other"
        ]):
            cat = "combination_restriction"
            verifiable = False

        # 3. Exclusion
        elif any(k in lower for k in [
            "defaulter", "bank default", "ineligible", "not eligible", "disqualified",
            "shall not be eligible", "excluding", "shall not", "income tax payer", "taxpayer",
            "government employee", "govt servant", "regular employment", "pucca house", "four wheeler"
        ]):
            # Ignore standard demographic lines
            if not ("between" in lower and "years" in lower) and not ("income" in lower and "lakh" in lower):
                cat = "exclusion"
                verifiable = False

        # 4. Documentation
        elif any(k in lower for k in [
            "certificate of", "ration card", "income certificate", "caste certificate",
            "domicile certificate", "land record", "khasra", "khatauni", "ror", "trade license",
            "disability certificate", "medical certificate", "bonafide certificate"
        ]):
            cat = "documentation"
            verifiable = False

        # 5. Procedural
        elif any(k in lower for k in [
            "contribute", "project cost", "margin money", "mandatory training", "edp training",
            "physical inspection", "verification by", "renewal every", "annual verification",
            "biometric", "inspection committee", "approval by", "deadline"
        ]):
            cat = "procedural"
            verifiable = False

        if cat and line not in seen_texts:
            seen_texts.add(line)
            conditions.append({
                "text": line,
                "category": cat,
                "verifiable_from_profile": verifiable,
            })

    return conditions


def process_all_fine_print(data_path: str = DATA_FILE):
    """Processes all schemes in dataset, extracts fine print, and persists back to JSON."""
    if not os.path.exists(data_path):
        logger.error(f"File not found: {data_path}")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        schemes = json.load(f)

    logger.info(f"Extracting fine-print conditions across {len(schemes)} schemes...")

    schemes_with_fp = 0
    total_fp_extracted = 0

    for scheme in schemes:
        conditions = extract_scheme_fine_print(scheme)
        scheme["fine_print_conditions"] = conditions
        if conditions:
            schemes_with_fp += 1
            total_fp_extracted += len(conditions)

    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(schemes, f, indent=2, ensure_ascii=False)

    logger.info("Fine print extraction complete!")
    logger.info(f"Schemes with fine-print conditions: {schemes_with_fp} / {len(schemes)} ({schemes_with_fp/len(schemes)*100:.1f}%)")
    logger.info(f"Total fine-print conditions captured: {total_fp_extracted}")


if __name__ == "__main__":
    process_all_fine_print()
