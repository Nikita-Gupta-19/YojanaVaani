"""
Extraction and quality audit script for YojanaVaani Phase 2.

Generates a comprehensive report covering:
1. Geographic audit:
   - Total schemes
   - Central Government count
   - Delhi Government count
   - Uttar Pradesh Government count
   - Excluded other-state/UT count (must be 0)
   - Confirmation of 100% in-scope jurisdiction
2. Category audit:
   - Distribution across all 9 target categories
3. Scheme-type audit:
   - Breakdown across intervention types:
     welfare_scheme, price_support_mechanism (MSP), procurement_program,
     credit_support, insurance_program, subsidized_inputs, social_security,
     employment_program, public_distribution_program, infrastructure_program
4. Completeness audit:
   - Population rate of description, benefits, complete eligibility text,
     fine-print conditions, required documents, application process, and source URL.
"""

import json
import os
import re
import sys
from collections import Counter
from typing import List, Dict, Any

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "scraped_schemes.json")
ALLOWED_GOVERNMENTS = {"Central Government", "Delhi Government", "Uttar Pradesh Government"}

TARGET_CATEGORIES = [
    "Agriculture & Farmers",
    "Water & Sanitation",
    "Electricity & Energy",
    "Food Security & Public Distribution",
    "Labour, Employment & Worker Welfare",
    "Education & Learning",
    "Women & Child",
    "Health & Wellness",
    "Housing & Shelter",
]

TARGET_SCHEME_TYPES = [
    "welfare_scheme",
    "price_support_mechanism",
    "procurement_program",
    "credit_support",
    "insurance_program",
    "subsidized_inputs",
    "social_security",
    "employment_program",
    "public_distribution_program",
    "infrastructure_program",
]


def load_schemes(data_path: str = DATA_FILE) -> List[Dict[str, Any]]:
    if not os.path.exists(data_path):
        print(f"Error: {data_path} does not exist.")
        sys.exit(1)
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def audit():
    schemes = load_schemes()
    total = len(schemes)

    print("\n" + "=" * 76)
    print(f"       YOJANAVAANI PHASE 2 KNOWLEDGE BASE AUDIT REPORT ({total} SCHEMES)")
    print("=" * 76 + "\n")

    # -------------------------------------------------------------
    # 1. GEOGRAPHIC AUDIT
    # -------------------------------------------------------------
    gov_counts = Counter()
    excluded_states = Counter()
    for s in schemes:
        gov = s.get("government_name", "Unknown")
        gov_counts[gov] += 1
        if gov not in ALLOWED_GOVERNMENTS:
            excluded_states[gov] += 1

    central_cnt = gov_counts.get("Central Government", 0)
    delhi_cnt = gov_counts.get("Delhi Government", 0)
    up_cnt = gov_counts.get("Uttar Pradesh Government", 0)
    excluded_cnt = sum(excluded_states.values())

    print("1. GEOGRAPHIC AUDIT:")
    print(f"   • Total Schemes:                 {total}")
    print(f"   • Central Government:            {central_cnt} ({central_cnt/total*100:.1f}%)" if total else "0")
    print(f"   • Delhi Government:              {delhi_cnt} ({delhi_cnt/total*100:.1f}%)" if total else "0")
    print(f"   • Uttar Pradesh Government:      {up_cnt} ({up_cnt/total*100:.1f}%)" if total else "0")
    print(f"   • Excluded Other-State/UT Count: {excluded_cnt} (Target: 0)")
    if excluded_cnt == 0:
        print("   ✓ CONFIRMATION: 100% of schemes belong exclusively to Central, Delhi, or UP.")
    else:
        print(f"   ✗ WARNING: {excluded_cnt} schemes belong to unauthorized jurisdictions: {dict(excluded_states)}")
    print()

    # -------------------------------------------------------------
    # 2. CATEGORY AUDIT (9 Target Categories)
    # -------------------------------------------------------------
    cat_counts = Counter()
    for s in schemes:
        cat = s.get("category", "Uncategorized")
        cat_counts[cat] += 1

    print("2. CATEGORY AUDIT (9 Target Categories):")
    for cat in TARGET_CATEGORIES:
        cnt = cat_counts.get(cat, 0)
        pct = (cnt / total * 100) if total else 0
        bar = "█" * int(pct / 2)
        print(f"   • {cat:<36} {cnt:>3} ({pct:>5.1f}%)  {bar}")
    other_cats = {k: v for k, v in cat_counts.items() if k not in TARGET_CATEGORIES}
    if other_cats:
        print(f"   • Other/Unclassified Categories: {other_cats}")
    print()

    # -------------------------------------------------------------
    # 3. SCHEME-TYPE AUDIT (Intervention Classification)
    # -------------------------------------------------------------
    type_counts = Counter()
    for s in schemes:
        st = s.get("scheme_type", "unclassified")
        type_counts[st] += 1

    print("3. SCHEME-TYPE & INTERVENTION AUDIT:")
    for st in TARGET_SCHEME_TYPES:
        cnt = type_counts.get(st, 0)
        pct = (cnt / total * 100) if total else 0
        print(f"   • {st:<30} {cnt:>3} ({pct:>5.1f}%)")
    other_types = {k: v for k, v in type_counts.items() if k not in TARGET_SCHEME_TYPES}
    if other_types:
        print(f"   • Other Types: {other_types}")
    print()

    # -------------------------------------------------------------
    # 4. COMPLETENESS AUDIT
    # -------------------------------------------------------------
    desc_pop = sum(1 for s in schemes if s.get("description") and len(s["description"]) > 20)
    benefits_pop = sum(1 for s in schemes if s.get("benefits") and len(s["benefits"]) > 10)
    elig_text_pop = sum(1 for s in schemes if s.get("eligibility_criteria", {}).get("other_conditions_text") and len(s["eligibility_criteria"]["other_conditions_text"]) > 10)
    docs_pop = sum(1 for s in schemes if s.get("required_documents") and len(s["required_documents"]) > 0)
    app_proc_pop = sum(1 for s in schemes if s.get("application_process") and len(s["application_process"]) > 10)
    source_url_pop = sum(1 for s in schemes if s.get("source_url") and s["source_url"].startswith("http"))
    fine_print_pop = sum(1 for s in schemes if s.get("fine_print_conditions") and len(s["fine_print_conditions"]) > 0)

    print("4. COMPLETENESS & DATA QUALITY AUDIT:")
    print(f"   • Description:                  {desc_pop:>3}/{total} ({desc_pop/total*100:.1f}%)")
    print(f"   • Benefits Text:                {benefits_pop:>3}/{total} ({benefits_pop/total*100:.1f}%)")
    print(f"   • Complete Eligibility Text:    {elig_text_pop:>3}/{total} ({elig_text_pop/total*100:.1f}%)")
    print(f"   • Required Documents:           {docs_pop:>3}/{total} ({docs_pop/total*100:.1f}%)")
    print(f"   • Application Process:          {app_proc_pop:>3}/{total} ({app_proc_pop/total*100:.1f}%)")
    print(f"   • Fine-Print Conditions:        {fine_print_pop:>3}/{total} ({fine_print_pop/total*100:.1f}%)")
    print(f"   • Source URL Traceability:      {source_url_pop:>3}/{total} ({source_url_pop/total*100:.1f}%)")
    print()

    # -------------------------------------------------------------
    # 5. STRUCTURED ELIGIBILITY FIELD STATS
    # -------------------------------------------------------------
    income_pop = sum(1 for s in schemes if s.get("eligibility_criteria", {}).get("income_ceiling") is not None)
    min_age_pop = sum(1 for s in schemes if s.get("eligibility_criteria", {}).get("min_age") is not None)
    max_age_pop = sum(1 for s in schemes if s.get("eligibility_criteria", {}).get("max_age") is not None)
    gender_female = sum(1 for s in schemes if s.get("eligibility_criteria", {}).get("gender") == "Female")
    occ_pop = sum(1 for s in schemes if s.get("eligibility_criteria", {}).get("occupation") is not None)
    pwd_true = sum(1 for s in schemes if s.get("eligibility_criteria", {}).get("disability_status") is True)

    print("5. STRUCTURED CORE ELIGIBILITY STATS:")
    print(f"   • Income Ceiling Populated:     {income_pop:>3}/{total} ({income_pop/total*100:.1f}%)")
    print(f"   • Min Age Populated:            {min_age_pop:>3}/{total} ({min_age_pop/total*100:.1f}%)")
    print(f"   • Max Age Populated:            {max_age_pop:>3}/{total} ({max_age_pop/total*100:.1f}%)")
    print(f"   • Female-Only Schemes:          {gender_female:>3}/{total} ({gender_female/total*100:.1f}%)")
    print(f"   • Specific Occupation:          {occ_pop:>3}/{total} ({occ_pop/total*100:.1f}%)")
    print(f"   • Disability Mandatory (PWD):   {pwd_true:>3}/{total} ({pwd_true/total*100:.1f}%)")
    print()

    # -------------------------------------------------------------
    # 6. HTML ENTITY CORRUPTION CHECK
    # -------------------------------------------------------------
    entity_corrupted = 0
    for s in schemes:
        dumped = json.dumps(s)
        if any(e in dumped for e in ["&amp;", "&#39;", "&quot;", "&gt;", "&lt;"]):
            entity_corrupted += 1

    print("6. TEXT SANITIZATION & INTEGRITY:")
    print(f"   • HTML Entity Artifacts:        {entity_corrupted} (Target: 0)")
    if entity_corrupted == 0:
        print("   ✓ All text is cleanly unescaped and formatted.")
    else:
        print("   ✗ Run clean_text.py to eliminate remaining raw entities.")
    print("=" * 76 + "\n")


if __name__ == "__main__":
    audit()
