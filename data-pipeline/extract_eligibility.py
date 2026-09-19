"""
Structured eligibility criteria extraction and scheme classification for YojanaVaani Phase 2.

Key Responsibilities:
1. Populates core structured fields:
   - min_age, max_age, income_ceiling
   - applicable_states, social_category, gender, occupation, disability_status
   - state_restriction, residence_requirement
2. Preserves the COMPLETE original official text in eligibility_criteria.other_conditions_text.
3. Classifies schemes into the 9 target categories with whole-word regex boundaries:
   - Agriculture & Farmers
   - Water & Sanitation
   - Electricity & Energy
   - Food Security & Public Distribution
   - Labour, Employment & Worker Welfare
   - Education & Learning
   - Women & Child
   - Health & Wellness
   - Housing & Shelter
4. Accurately determines scheme_type:
   - price_support_mechanism (MSP)
   - procurement_program (food grains, produce)
   - insurance_program (crop, health, accident)
   - credit_support (KCC, loan subvention)
   - subsidized_inputs (fertilizer, seeds, solar pumps)
   - social_security (pensions, disability aid, ex-gratia)
   - employment_program (MGNREGA, internships)
   - public_distribution_program (NFSA, ration)
   - infrastructure_program (toilets, housing, water tap)
   - welfare_scheme
5. Strictly differentiates hard eligibility REQUIREMENTS from PREFERENCES/PRIORITIES (e.g. PWD priority != disability_status: True).
"""

import json
import logging
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

load_dotenv()

# Add project root and backend to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

try:
    from app.core.config import settings
    OLLAMA_BASE_URL = settings.OLLAMA_BASE_URL
    OLLAMA_MODEL = settings.OLLAMA_MODEL
except Exception:
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

from clean_text import clean_text

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "scraped_schemes.json")


class StructuredEligibility(BaseModel):
    min_age: Optional[int] = Field(default=None, description="Minimum age in years or null")
    max_age: Optional[int] = Field(default=None, description="Maximum age in years or null")
    income_ceiling: Optional[float] = Field(default=None, description="Maximum annual family income in Rupees or null")
    applicable_states: List[str] = Field(default_factory=lambda: ["All"], description="Applicable Indian states/UTs or ['All']")
    social_category: List[str] = Field(default_factory=lambda: ["All"], description="Eligible social categories (SC, ST, OBC, EWS, etc.) or ['All']")
    gender: Optional[str] = Field(default="All", description="'Female', 'Male', or 'All'")
    occupation: Optional[str] = Field(default=None, description="Required occupation or null")
    disability_status: Optional[bool] = Field(default=None, description="True ONLY if disability is a mandatory requirement. Null if preference or not required.")
    state_restriction: Optional[str] = Field(default=None, description="Specific state restriction if state-specific, else null")
    residence_requirement: Optional[str] = Field(default=None, description="Specific residence requirement (e.g. resident of Delhi for 3 years) or null")
    extraction_method: str = Field(default="llm", description="'llm' or 'regex_fallback'")
    other_conditions_text: str = Field(default="", description="Full complete cleaned conditions text")


def classify_scheme_category(name: str, desc: str, raw_categories: List[str]) -> Tuple[str, List[str]]:
    """
    Classifies a scheme into one of the 9 target categories using whole-word regex patterns.
    Returns (primary_category, list_of_all_applicable_categories).
    """
    text = f"{name} {desc}".lower()
    cats_set = set()

    # 1. Water & Sanitation
    if re.search(r'\b(drinking water|jal jeevan|water supply|rural water|tap connection|sanitation|toilet|toilets|swachh bharat|ihhl|latrine|sewerage|jal hauj|shauchalaya)\b', text):
        cats_set.add("Water & Sanitation")

    # 2. Electricity & Energy
    if re.search(r'\b(solar|surya ghar|kusum|electricity|electrification|saubhagya|clean cooking|ujjwala|lpg subsidy|power supply|biogas|rooftop solar)\b', text):
        cats_set.add("Electricity & Energy")

    # 3. Food Security & Public Distribution
    if re.search(r'\b(ration card|ration cards|ration shop|fair price shop|nfsa|food security|pds|antyodaya|annapurna|pmgkay|food grain|food grains|pulses distribution|mid day meal|poshan|shram ann)\b', text):
        cats_set.add("Food Security & Public Distribution")

    # 4. Agriculture & Farmers
    if re.search(r'\b(farmer|farmers|kisan|crop|crops|agriculture|agricultural|msp|support price|procurement of food grains|pm-kisan|fasal bima|krishi|irrigation|fertilizer|soil health|agricultural loan|kcc|farm equipment|horticulture|fisheries|aromatic plants)\b', text):
        cats_set.add("Agriculture & Farmers")

    # 5. Education & Learning
    if re.search(r'\b(scholarship|scholarships|education|educational|student|students|school|schools|university|fellowship|stipend|vidya|vidyala|matric|tuition|coaching|degree|shiksha|pustak)\b', text):
        cats_set.add("Education & Learning")

    # 6. Women & Child
    if re.search(r'\b(women|female|girl|girls|child|children|maternity|widow|widows|sukanya|matru vandana|beti|mahila|destitute women|kanya|bal seva|miscarriage|orphan girls)\b', text):
        cats_set.add("Women & Child")

    # 7. Health & Wellness
    if re.search(r'\b(health|medical|ayushman|arogya|hospital|hospitals|disease|treatment|disability|disabled|pwds|divyang|surgical grant|wellness|illness|prosthetic|artificial limbs|tricycle|leprosy)\b', text):
        cats_set.add("Health & Wellness")

    # 8. Housing & Shelter
    if re.search(r'\b(housing|house|houses|awas|awaas|shelter|shelters|pucca house|slum|homeless|rain basera|residential|construction of house)\b', text):
        cats_set.add("Housing & Shelter")

    # 9. Labour, Employment & Worker Welfare
    if re.search(r'\b(mgnrega|shram|shramik|labour|labor|worker|workers|employment|unemployment|berojgari|rozgar|rojgar|bocw|construction worker|unorganized worker|artisan|artisans|weaver|weavers|vishwakarma|naps|apprenticeship|internship|skill development|kaushal|sports person)\b', text):
        cats_set.add("Labour, Employment & Worker Welfare")

    # Priority resolution if multiple
    if not cats_set:
        # Fallback to myScheme raw categories
        for rc in raw_categories:
            if "Agriculture" in rc:
                cats_set.add("Agriculture & Farmers")
            elif "Education" in rc:
                cats_set.add("Education & Learning")
            elif "Women" in rc:
                cats_set.add("Women & Child")
            elif "Health" in rc:
                cats_set.add("Health & Wellness")
            elif "Housing" in rc:
                cats_set.add("Housing & Shelter")
            elif "Employment" in rc or "Skills" in rc:
                cats_set.add("Labour, Employment & Worker Welfare")

    if not cats_set:
        cats_set.add("Labour, Employment & Worker Welfare")

    # Primary category ordering based on specific domain keywords in title
    title_lower = name.lower()
    for cat in ["Water & Sanitation", "Electricity & Energy", "Food Security & Public Distribution",
                "Agriculture & Farmers", "Education & Learning", "Women & Child",
                "Health & Wellness", "Housing & Shelter", "Labour, Employment & Worker Welfare"]:
        if cat in cats_set:
            # If title explicitly matches this category, pick it as primary
            if cat == "Water & Sanitation" and any(k in title_lower for k in ["water", "jal", "sanitation", "toilet", "shauchalaya"]):
                return cat, list(cats_set)
            if cat == "Electricity & Energy" and any(k in title_lower for k in ["solar", "surya", "kusum", "bijli", "electricity", "ujjwala"]):
                return cat, list(cats_set)
            if cat == "Food Security & Public Distribution" and any(k in title_lower for k in ["ration", "food", "nfsa", "antyodaya", "ann"]):
                return cat, list(cats_set)
            if cat == "Agriculture & Farmers" and any(k in title_lower for k in ["farmer", "kisan", "crop", "krishi", "msp", "support price", "kcc"]):
                return cat, list(cats_set)
            if cat == "Education & Learning" and any(k in title_lower for k in ["scholarship", "education", "student", "shiksha", "vidya", "matric"]):
                return cat, list(cats_set)
            if cat == "Women & Child" and any(k in title_lower for k in ["women", "girl", "widow", "mahila", "kanya", "matru", "maternity"]):
                return cat, list(cats_set)
            if cat == "Health & Wellness" and any(k in title_lower for k in ["health", "arogya", "medical", "treatment", "disability", "divyang", "limbs", "disease"]):
                return cat, list(cats_set)
            if cat == "Housing & Shelter" and any(k in title_lower for k in ["awas", "awaas", "housing", "house", "shelter"]):
                return cat, list(cats_set)

    primary = list(cats_set)[0]
    return primary, list(cats_set)


def classify_scheme_type(name: str, desc: str, benefits: str) -> str:
    """Classifies intervention into precise scheme_type."""
    combined = f"{name} {desc} {benefits}".lower()

    if re.search(r'\b(minimum support price|msp|price support scheme|market intervention)\b', combined):
        return "price_support_mechanism"
    if re.search(r'\b(procurement of food grains|procurement at support price|direct procurement)\b', combined):
        return "procurement_program"
    if re.search(r'\b(fasal bima|crop insurance|insurance scheme|life insurance|accident insurance|suraksha bima|jeevan jyoti)\b', combined):
        return "insurance_program"
    if re.search(r'\b(credit card|kcc|interest subvention|subvention on loan|collateral free loan|loan scheme|education loan)\b', combined):
        return "credit_support"
    if re.search(r'\b(fertilizer subsidy|seed subsidy|solar pump subsidy|subsidized equipment|machinery subsidy|grant for equipment)\b', combined):
        return "subsidized_inputs"
    if re.search(r'\b(pension|old age pension|widow pension|disability pension|family pension|ex-gratia|family benefit|survivor grant)\b', combined):
        return "social_security"
    if re.search(r'\b(mgnrega|employment guarantee|wage employment|apprenticeship|internship programme|internship scheme|berojgari bhatta)\b', combined):
        return "employment_program"
    if re.search(r'\b(nfsa|ration card|targeted public distribution|antyodaya anna|food grain distribution|distribution of pulses)\b', combined):
        return "public_distribution_program"
    if re.search(r'\b(tap water connection|toilet construction|shauchalaya|pucca house construction|shelter board|housing for)\b', combined):
        return "infrastructure_program"

    return "welfare_scheme"


def extract_eligibility_regex(text: str, gov_name: str, beneficiary_states: list = None) -> StructuredEligibility:
    """
    Enhanced regex parser for structured eligibility extraction.
    Ensures complete conditions text is preserved in other_conditions_text.
    """
    cleaned_text = clean_text(text)
    text_lower = cleaned_text.lower()

    # 1. Age extraction
    min_age = None
    max_age = None
    range_match = re.search(r'(?:age|aged|between)?\s*(\d{1,2})\s*(?:to|-|and)\s*(\d{1,2})\s*years?', text_lower)
    if range_match:
        min_age = int(range_match.group(1))
        max_age = int(range_match.group(2))
    else:
        min_match = re.search(r'(?:minimum age|at least|above|greater than|attained the age of|more than)\s*(\d{1,2})\s*years?', text_lower)
        if min_match:
            min_age = int(min_match.group(1))
        max_match = re.search(r'(?:maximum age|up to|below|less than|not exceeding)\s*(\d{1,2})\s*years?', text_lower)
        if max_match:
            max_age = int(max_match.group(1))

    # 2. Income ceiling extraction
    income_ceiling = None
    lakh_match = re.search(r'(?:income|family income|annual income)?\s*(?:must not exceed|should not exceed|not exceed|is|up to|less than|below|ceiling of)?\s*(?:rs\.?|₹|inr)?\s*([\d\.]+)\s*(?:lakh|lac|lakhs|lacs)', text_lower)
    if lakh_match:
        try:
            income_ceiling = float(lakh_match.group(1)) * 100000.0
        except ValueError:
            pass
    if income_ceiling is None:
        direct_match = re.search(r'(?:income|family income|annual income)\s*(?:must not exceed|should not exceed|not exceed|is|up to|less than|below)?\s*(?:rs\.?|₹|inr)?\s*([\d,]+)\b', text_lower)
        if direct_match:
            raw_str = direct_match.group(1).replace(",", "")
            try:
                val = float(raw_str)
                if val >= 10000:
                    income_ceiling = val
            except ValueError:
                pass

    # 3. Social Category detection (affirmative requirement only)
    social_categories = []
    for cat in ["SC", "ST", "OBC", "EWS", "BPL", "Minority"]:
        if re.search(rf'(?<!excluding\s)(?<!except\s)\b{cat.lower()}\b', text_lower):
            social_categories.append(cat)
    if not social_categories:
        social_categories = ["All"]

    # 4. Gender detection (Female only if women-exclusive)
    gender = "All"
    women_exclusive = bool(re.search(r'\b(?:women only|female only|girl child only|widow|pregnant women|lactating mothers|for women|for girls|mothers)\b', text_lower))
    men_mentioned = bool(re.search(r'\b(?:men and women|male and female|boys and girls|both men and women)\b', text_lower))
    if women_exclusive and not men_mentioned:
        gender = "Female"

    # 5. Occupation detection
    occupation = None
    for occ in ["Farmer", "Student", "Artisan", "Unemployed", "Weaver", "Fisherman", "Self-Employed", "Laborer", "Worker"]:
        if occ.lower() in text_lower:
            occupation = occ
            break

    # 6. Disability status: STRICT requirement vs preference
    disability_status = None
    has_pwd = bool(re.search(r'\b(?:disability|disabled|pwd|differently abled|divyang)\b', text_lower))
    is_pwd_priority = bool(re.search(r'\b(?:given priority|preference|higher subsidy|additional subsidy|concession)\b', text_lower))
    is_pwd_exclusive = bool(re.search(r'\b(?:must be disabled|only for disabled|persons with disability only|100% disabled|benchmark disability|disability certificate required)\b', text_lower))
    if has_pwd and (is_pwd_exclusive or not is_pwd_priority):
        if is_pwd_exclusive or "pension to disabled" in text_lower or "rehabilitation of pwds" in text_lower:
            disability_status = True

    # 7. State restriction
    state_restriction = None
    if "Delhi" in gov_name or "delhi" in text_lower:
        state_restriction = "Delhi"
    elif "Uttar Pradesh" in gov_name or "uttar pradesh" in text_lower:
        state_restriction = "Uttar Pradesh"

    # 8. Residence requirement
    residence_req = None
    res_match = re.search(r'(?:resident of|residing in|domicile of)\s*([A-Za-z\s]+)(?:for at least|for minimum|for)?\s*(\d{1,2}\s*years?)?', text_lower)
    if res_match:
        residence_req = res_match.group(0).strip()

    states = [s for s in (beneficiary_states or []) if s != "All"]

    return StructuredEligibility(
        min_age=min_age,
        max_age=max_age,
        income_ceiling=income_ceiling,
        applicable_states=states if states else ["All"],
        social_category=social_categories,
        gender=gender,
        occupation=occupation,
        disability_status=disability_status,
        state_restriction=state_restriction,
        residence_requirement=residence_req,
        extraction_method="regex_fallback",
        other_conditions_text=cleaned_text,
    )


def extract_all():
    if not os.path.exists(DATA_FILE):
        logger.error(f"Data file not found: {DATA_FILE}")
        sys.exit(1)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        schemes = json.load(f)

    logger.info(f"Extracting structured eligibility and classifying {len(schemes)} schemes...")

    updated_schemes = []
    for s in schemes:
        name = s.get("name", "")
        desc = s.get("description", "")
        benefits = s.get("benefits", "")
        raw_cats = s.get("categories", [s.get("category", "")])
        gov_name = s.get("government_name", "Central Government")

        # Refine category & categories list
        primary_cat, all_cats = classify_scheme_category(name, desc, raw_cats)
        s["category"] = primary_cat
        s["categories"] = all_cats

        # Refine scheme_type
        s["scheme_type"] = classify_scheme_type(name, desc, benefits)

        # Extract eligibility
        elig_data = s.get("eligibility_criteria", {})
        cond_text = elig_data.get("other_conditions_text") or desc

        beneficiary_states = elig_data.get("applicable_states", ["All"])
        parsed_elig = extract_eligibility_regex(cond_text, gov_name, beneficiary_states)
        s["eligibility_criteria"] = parsed_elig.model_dump()

        updated_schemes.append(s)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_schemes, f, indent=2, ensure_ascii=False)

    logger.info(f"Structured extraction and classification complete! Updated {len(updated_schemes)} schemes in {DATA_FILE}")


if __name__ == "__main__":
    extract_all()
