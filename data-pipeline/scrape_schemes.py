"""
Harvesting and scraping script for YojanaVaani Phase 2.
Scrapes official government schemes from https://www.myscheme.gov.in/

Scope & Filtering:
- Central Government
- Delhi Government
- Uttar Pradesh Government
Excludes schemes belonging exclusively to any other state or UT.

Expanded 9 Categories:
1. Agriculture & Farmers (including MSP & price support)
2. Water & Sanitation
3. Electricity & Energy
4. Food Security & Public Distribution
5. Labour, Employment & Worker Welfare
6. Education & Learning
7. Women & Child
8. Health & Wellness
9. Housing & Shelter
"""

import json
import logging
import os
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv

load_dotenv()

# Add project root and backend to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

try:
    from app.core.config import settings
    DEFAULT_API_KEY = settings.MYSCHEME_API_KEY
except Exception:
    DEFAULT_API_KEY = "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"

API_KEY = os.getenv("MYSCHEME_API_KEY", DEFAULT_API_KEY)
BASE_URL = "https://api.myscheme.gov.in"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "x-api-key": API_KEY,
    "Origin": "https://www.myscheme.gov.in",
    "Referer": "https://www.myscheme.gov.in/",
}

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "scraped_schemes.json")

ctx = ssl._create_unverified_context()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Allowed jurisdictions
ALLOWED_GOVERNMENTS = {
    "Central Government",
    "Delhi Government",
    "Uttar Pradesh Government",
}


def make_request(url: str, method: str = "GET", body: bytes = None) -> Optional[dict]:
    req = urllib.request.Request(url, data=body, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        logger.warning(f"Request failed for {url}: {e}")
    return None


def extract_slate_text(slate_nodes) -> str:
    """Recursively extract clean plain text from Slate.js AST nodes."""
    if not slate_nodes:
        return ""
    if isinstance(slate_nodes, str):
        return slate_nodes
    if isinstance(slate_nodes, list):
        return "\n".join(extract_slate_text(item) for item in slate_nodes).strip()
    if isinstance(slate_nodes, dict):
        text = slate_nodes.get("text", "")
        children = slate_nodes.get("children", [])
        if children:
            child_text = extract_slate_text(children)
            if text:
                return f"{text} {child_text}".strip()
            return child_text
        return text
    return str(slate_nodes)


def determine_jurisdiction(fields: dict, basic_details: dict) -> Tuple[Optional[str], Optional[str]]:
    """
    Determines (government_level, government_name).
    Returns (None, None) if scheme belongs exclusively to an excluded state/UT.
    """
    raw_level = fields.get("level") or basic_details.get("level")
    if isinstance(raw_level, dict):
        raw_level = raw_level.get("value") or raw_level.get("label")
    level_str = str(raw_level or "").strip().lower()

    states = fields.get("beneficiaryState") or basic_details.get("beneficiaryState") or []
    if isinstance(states, str):
        states = [states]
    states_lower = [str(s).lower() for s in states]

    # Central scheme check
    if level_str == "central" or "all" in states_lower or not states:
        return "Central", "Central Government"

    # State scheme check - only Delhi and Uttar Pradesh allowed
    if any("delhi" in s for s in states_lower) or "nct of delhi" in states_lower:
        return "State", "Delhi Government"
    if any("uttar pradesh" in s or "up" == s for s in states_lower):
        return "State", "Uttar Pradesh Government"

    # Name-based check for state
    scheme_name = (basic_details.get("schemeName") or fields.get("schemeName", "")).lower()
    if "delhi" in scheme_name:
        return "State", "Delhi Government"
    if "uttar pradesh" in scheme_name:
        return "State", "Uttar Pradesh Government"

    # Any other state is excluded
    return None, None


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
    if re.search(r'\b(farmer|farmers|kisan|crop|crops|agriculture|agricultural|msp|support price|procurement of food grains|pm-kisan|fasal bima|krishi|irrigation|fertilizer|soil health|agricultural loan|kcc|farm equipment|horticulture|fisheries|aromatic plants|gau samvardhan|pashupalak)\b', text):
        cats_set.add("Agriculture & Farmers")

    # 5. Education & Learning
    if re.search(r'\b(scholarship|scholarships|education|educational|student|students|school|schools|university|fellowship|stipend|vidya|vidyala|matric|tuition|coaching|degree|shiksha|pustak)\b', text):
        cats_set.add("Education & Learning")

    # 6. Women & Child
    if re.search(r'\b(women|female|girl|girls|child|children|maternity|widow|widows|sukanya|matru vandana|beti|mahila|destitute women|kanya|bal seva|miscarriage|orphan girls)\b', text):
        cats_set.add("Women & Child")

    # 7. Health & Wellness
    if re.search(r'\b(health|medical|ayushman|arogya|hospital|hospitals|disease|treatment|disability|disabled|pwds|divyang|surgical grant|wellness|illness|prosthetic|artificial limbs|tricycle|leprosy|bimari)\b', text):
        cats_set.add("Health & Wellness")

    # 8. Housing & Shelter
    if re.search(r'\b(housing|house|houses|awas|awaas|shelter|shelters|pucca house|slum|homeless|rain basera|residential|construction of house)\b', text):
        cats_set.add("Housing & Shelter")

    # 9. Labour, Employment & Worker Welfare
    if re.search(r'\b(mgnrega|shram|shramik|labour|labor|worker|workers|employment|unemployment|berojgari|rozgar|rojgar|bocw|construction worker|unorganized worker|artisan|artisans|weaver|weavers|vishwakarma|naps|apprenticeship|internship|skill development|kaushal|sports person)\b', text):
        cats_set.add("Labour, Employment & Worker Welfare")

    if not cats_set:
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

    title_lower = name.lower()
    for cat in ["Water & Sanitation", "Electricity & Energy", "Food Security & Public Distribution",
                "Agriculture & Farmers", "Education & Learning", "Women & Child",
                "Health & Wellness", "Housing & Shelter", "Labour, Employment & Worker Welfare"]:
        if cat in cats_set:
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
            if cat == "Health & Wellness" and any(k in title_lower for k in ["health", "arogya", "medical", "treatment", "disability", "divyang", "limbs", "disease", "bimari"]):
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


def parse_eligibility_fields(eligibility_md: str, beneficiary_states: list) -> dict:
    """Extracts structured core eligibility fields while keeping complete text."""
    text_lower = eligibility_md.lower()

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

    social_categories = []
    for cat in ["SC", "ST", "OBC", "General", "EWS", "BPL", "Minority"]:
        if re.search(rf'\b{cat.lower()}\b', text_lower):
            social_categories.append(cat)
    if not social_categories:
        social_categories = ["All"]

    gender = "All"
    is_women_only = bool(re.search(r'\b(?:women only|girl child|female only|widow|pregnant women|lactating mothers|for women|for girls|mothers)\b', text_lower))
    if is_women_only or "girl" in text_lower or "women" in text_lower:
        if not ("men and women" in text_lower or "male and female" in text_lower):
            gender = "Female"

    occupation = None
    for occ in ["Farmer", "Student", "Artisan", "Unemployed", "Weaver", "Fisherman", "Self-Employed", "Laborer", "Worker"]:
        if occ.lower() in text_lower:
            occupation = occ
            break

    # PWD status: True ONLY if disability is an explicit requirement
    disability_status = None
    if re.search(r'\b(?:must be disabled|person with disability|minimum 40% disability|disability certificate required|for disabled persons|for pwds)\b', text_lower):
        disability_status = True

    states = [s for s in beneficiary_states if s != "All"] if beneficiary_states else []

    return {
        "min_age": min_age,
        "max_age": max_age,
        "income_ceiling": income_ceiling,
        "applicable_states": states if states else ["All"],
        "social_category": social_categories,
        "gender": gender,
        "occupation": occupation,
        "disability_status": disability_status,
        "other_conditions_text": eligibility_md.strip(),
    }


def fetch_scheme_detail(slug: str, fallback_fields: dict) -> Optional[dict]:
    """Fetches full scheme detail, documents, application process, and references."""
    detail_url = f"{BASE_URL}/schemes/v6/public/schemes?slug={slug}&lang=en"
    detail_resp = make_request(detail_url)
    if not detail_resp or not isinstance(detail_resp.get("data"), dict):
        return None

    data = detail_resp["data"]
    _id = data.get("_id")
    en = data.get("en", {})
    if not isinstance(en, dict):
        return None

    basic_details = en.get("basicDetails", {})
    scheme_content = en.get("schemeContent", {})
    eligibility_criteria_raw = en.get("eligibilityCriteria", {})

    gov_level, gov_name = determine_jurisdiction(fallback_fields, basic_details)
    if not gov_level:
        # Belongs exclusively to an excluded state/UT
        return None

    scheme_name = basic_details.get("schemeName") or fallback_fields.get("schemeName", slug)
    brief_desc = basic_details.get("briefDescription") or fallback_fields.get("briefDescription", "")
    detailed_desc = scheme_content.get("detailedDescription_md") or extract_slate_text(scheme_content.get("detailedDescription"))
    description = detailed_desc.strip() or brief_desc.strip()

    # Eligibility
    eligibility_md = eligibility_criteria_raw.get("eligibilityDescription_md") or ""
    if not eligibility_md:
        eligibility_md = extract_slate_text(eligibility_criteria_raw.get("eligibilityDescription"))
    if not eligibility_md:
        eligibility_md = brief_desc

    beneficiary_states = basic_details.get("beneficiaryState") or fallback_fields.get("beneficiaryState") or ["All"]
    if isinstance(beneficiary_states, str):
        beneficiary_states = [beneficiary_states]

    # Benefits
    benefits = scheme_content.get("benefits_md") or extract_slate_text(scheme_content.get("benefits"))
    if not benefits:
        benefits = brief_desc

    # Application process and URL
    app_proc_raw = en.get("applicationProcess", [])
    app_process_parts = []
    app_url = None
    if isinstance(app_proc_raw, list):
        for proc in app_proc_raw:
            mode = proc.get("mode", "")
            p_url = proc.get("url", "")
            if p_url and not app_url:
                app_url = p_url
            steps = extract_slate_text(proc.get("process", []))
            app_process_parts.append(f"Mode: {mode}\nURL: {p_url}\nSteps: {steps}".strip())
        application_process = "\n\n".join(app_process_parts)
    else:
        application_process = extract_slate_text(app_proc_raw)

    # Documents
    required_documents = []
    if _id:
        time.sleep(0.3)
        docs_url = f"{BASE_URL}/schemes/v6/public/schemes/{_id}/documents?lang=en"
        docs_resp = make_request(docs_url)
        if docs_resp and isinstance(docs_resp.get("data"), dict):
            docs_en = docs_resp["data"].get("en", {})
            if isinstance(docs_en, dict):
                docs_list_raw = docs_en.get("documents_required", [])
                doc_text = extract_slate_text(docs_list_raw)
                for line in doc_text.split("\n"):
                    clean_line = re.sub(r'^\d+[\.\)]\s*', '', line).strip()
                    if clean_line and len(clean_line) > 3:
                        required_documents.append(clean_line)

    # Guideline document URL from references
    guideline_doc_url = None
    references = scheme_content.get("references", []) or en.get("references", [])
    if isinstance(references, list):
        for ref in references:
            if isinstance(ref, dict):
                r_title = ref.get("title", "").lower()
                r_url = ref.get("url", "")
                if "guideline" in r_title or r_url.lower().endswith(".pdf"):
                    guideline_doc_url = r_url
                    break
        if not guideline_doc_url and references and isinstance(references[0], dict):
            guideline_doc_url = references[0].get("url")

    # Categories
    raw_cats = fallback_fields.get("schemeCategory") or []
    if isinstance(raw_cats, str):
        raw_cats = [raw_cats]
    primary_category, categories = classify_scheme_category(scheme_name, description, raw_cats)

    # Scheme Type
    scheme_type = classify_scheme_type(scheme_name, description, benefits)

    # Structured eligibility
    structured_eligibility = parse_eligibility_fields(eligibility_md, beneficiary_states)

    # Administrative
    ministry = basic_details.get("nodalMinistryName") or fallback_fields.get("nodalMinistryName")
    department = basic_details.get("nodalDepartmentName") or fallback_fields.get("nodalDepartmentName")

    return {
        "name": scheme_name.strip(),
        "slug": slug,
        "government_level": gov_level,
        "government_name": gov_name,
        "scheme_type": scheme_type,
        "category": primary_category,
        "categories": categories,
        "description": description.strip(),
        "ministry": ministry,
        "department": department,
        "implementing_agency": None,
        "ministry_or_department": ministry or department,
        "benefits": benefits.strip(),
        "eligibility_criteria": structured_eligibility,
        "required_documents": required_documents,
        "application_process": application_process.strip(),
        "application_url": app_url,
        "contact_information": None,
        "guideline_document_url": guideline_doc_url,
        "fine_print_conditions": [],
        "source_url": f"https://www.myscheme.gov.in/schemes/{slug}",
        "source_last_checked": datetime.now(timezone.utc).isoformat(),
        "last_scraped_at": datetime.now(timezone.utc).isoformat(),
        "source_text": f"Name: {scheme_name}\nCategory: {primary_category}\nDescription: {description}\nEligibility: {eligibility_md}\nBenefits: {benefits}\nDocuments: {', '.join(required_documents)}",
    }


def search_and_harvest(filter_query: list, keyword: str = "", limit: int = 30) -> List[dict]:
    """Executes a search query and yields hit item fields."""
    q_enc = urllib.parse.quote(json.dumps(filter_query))
    kw_enc = urllib.parse.quote(keyword)
    url = f"{BASE_URL}/search/v6/schemes?lang=en&q={q_enc}&keyword={kw_enc}&sort=&from=0&size={limit}"

    resp = make_request(url)
    if not resp or not isinstance(resp.get("data"), dict):
        return []
    return resp["data"].get("hits", {}).get("items", [])


def harvest_all() -> List[dict]:
    """Orchestrates comprehensive harvesting across Central, Delhi, and UP schemes."""
    schemes_by_slug: Dict[str, dict] = {}

    search_tasks = [
        # 1. State-specific filters (All Delhi & UP schemes available)
        ([{"identifier": "beneficiaryState", "value": "Delhi"}], "", 54),
        ([{"identifier": "beneficiaryState", "value": "Uttar Pradesh"}], "", 50),

        # 2. Targeted search queries for Central schemes across categories & interventions
        # Agriculture & Farmers & MSP
        ([{"identifier": "level", "value": "Central"}], "Price Support Scheme", 10),
        ([{"identifier": "level", "value": "Central"}], "Minimum Support Price", 10),
        ([{"identifier": "level", "value": "Central"}], "Procurement", 10),
        ([{"identifier": "level", "value": "Central"}], "PM-KISAN", 10),
        ([{"identifier": "level", "value": "Central"}], "Fasal Bima", 10),
        ([{"identifier": "level", "value": "Central"}], "Kisan Credit Card", 10),
        ([{"identifier": "level", "value": "Central"}], "Krishi Sinchayee", 10),

        # Water & Sanitation
        ([{"identifier": "level", "value": "Central"}], "Jal Jeevan", 10),
        ([{"identifier": "level", "value": "Central"}], "Swachh Bharat", 15),
        ([{"identifier": "level", "value": "Central"}], "Sanitation", 10),
        ([{"identifier": "level", "value": "Central"}], "Water Supply", 10),

        # Electricity & Energy
        ([{"identifier": "level", "value": "Central"}], "Surya Ghar", 10),
        ([{"identifier": "level", "value": "Central"}], "KUSUM", 10),
        ([{"identifier": "level", "value": "Central"}], "Ujjwala", 10),
        ([{"identifier": "level", "value": "Central"}], "Solar", 12),
        ([{"identifier": "level", "value": "Central"}], "Saubhagya", 8),

        # Food Security & Public Distribution
        ([{"identifier": "level", "value": "Central"}], "NFSA", 10),
        ([{"identifier": "level", "value": "Central"}], "Ration", 10),
        ([{"identifier": "level", "value": "Central"}], "Food Security", 10),
        ([{"identifier": "level", "value": "Central"}], "Antyodaya", 10),
        ([{"identifier": "level", "value": "Central"}], "Garib Kalyan", 10),

        # Labour, Employment & Worker Welfare
        ([{"identifier": "level", "value": "Central"}], "MGNREGA", 10),
        ([{"identifier": "level", "value": "Central"}], "Shram Yogi", 10),
        ([{"identifier": "level", "value": "Central"}], "BOCW", 10),
        ([{"identifier": "level", "value": "Central"}], "e-Shram", 8),
        ([{"identifier": "level", "value": "Central"}], "Vishwakarma", 8),
        ([{"identifier": "level", "value": "Central"}], "Apprenticeship", 8),

        # Education & Learning
        ([{"identifier": "level", "value": "Central"}], "Scholarship", 15),
        ([{"identifier": "level", "value": "Central"}], "Higher Education", 10),
        ([{"identifier": "level", "value": "Central"}], "Education Loan", 10),

        # Women & Child
        ([{"identifier": "level", "value": "Central"}], "Matru Vandana", 10),
        ([{"identifier": "level", "value": "Central"}], "Sukanya", 8),
        ([{"identifier": "level", "value": "Central"}], "Widow Pension", 10),
        ([{"identifier": "level", "value": "Central"}], "Women", 12),

        # Health & Wellness
        ([{"identifier": "level", "value": "Central"}], "Ayushman Bharat", 12),
        ([{"identifier": "level", "value": "Central"}], "Arogya", 10),
        ([{"identifier": "level", "value": "Central"}], "Disability Pension", 10),
        ([{"identifier": "level", "value": "Central"}], "Health", 12),

        # Housing & Shelter
        ([{"identifier": "level", "value": "Central"}], "Awas Yojana", 15),
        ([{"identifier": "level", "value": "Central"}], "Housing", 12),
    ]

    total_tasks = len(search_tasks)
    logger.info(f"Starting harvest across {total_tasks} targeted search queries...")

    for i, (f_query, keyword, limit) in enumerate(search_tasks, 1):
        kw_display = f"keyword='{keyword}'" if keyword else f"filter={f_query}"
        logger.info(f"[{i}/{total_tasks}] Harvesting: {kw_display} (limit {limit})")

        items = search_and_harvest(f_query, keyword, limit)
        for it in items:
            fields = it.get("fields", {})
            slug = fields.get("slug")
            if not slug:
                continue

            # Deduplication: If already scraped, check if we need to add a category
            if slug in schemes_by_slug:
                existing = schemes_by_slug[slug]
                raw_cats = fields.get("schemeCategory") or []
                if isinstance(raw_cats, str):
                    raw_cats = [raw_cats]
                for rc in raw_cats:
                    mapped_cat, _ = classify_scheme_category(existing["name"], existing["description"], [rc])
                    if mapped_cat not in existing["categories"]:
                        existing["categories"].append(mapped_cat)
                continue

            # Respect rate limit
            time.sleep(0.35)

            # Fetch detailed scheme page
            try:
                scheme_record = fetch_scheme_detail(slug, fields)
                if scheme_record:
                    schemes_by_slug[slug] = scheme_record
                    logger.info(f"  [+] Scraped: {scheme_record['name']} | Gov: {scheme_record['government_name']} | Type: {scheme_record['scheme_type']} | Cat: {scheme_record['category']}")
            except Exception as e:
                logger.warning(f"Error fetching detail for {slug}: {e}")
                continue

    return list(schemes_by_slug.values())


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    schemes = harvest_all()

    # Final validation of geographic constraint
    valid_schemes = [
        s for s in schemes if s.get("government_name") in ALLOWED_GOVERNMENTS
    ]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(valid_schemes, f, indent=2, ensure_ascii=False)

    logger.info("=" * 60)
    logger.info(f"Harvest complete! Successfully saved {len(valid_schemes)} schemes to {OUTPUT_FILE}")

    # Summary by government
    gov_counts = {}
    cat_counts = {}
    type_counts = {}
    for s in valid_schemes:
        gov = s.get("government_name", "Unknown")
        cat = s.get("category", "Unknown")
        stype = s.get("scheme_type", "Unknown")
        gov_counts[gov] = gov_counts.get(gov, 0) + 1
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
        type_counts[stype] = type_counts.get(stype, 0) + 1

    logger.info(f"Jurisdiction breakdown: {gov_counts}")
    logger.info(f"Category breakdown: {cat_counts}")
    logger.info(f"Scheme Type breakdown: {type_counts}")


if __name__ == "__main__":
    main()
