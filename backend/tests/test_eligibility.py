"""
Unit tests for Deterministic Eligibility Engine (Phase 6).

Verifies:
1. Age boundary enforcement (min_age and max_age).
2. Income ceiling & bracket compliance.
3. Social category reservation matching.
4. State geographic residency restrictions.
5. Gender criteria restrictions.
6. Disability mandate compliance.
7. Candidate ranking ordering (QUALIFIES first, NEEDS_MORE_INFO second, DOES_NOT_QUALIFY last).
"""

import pytest
from app.services.eligibility_engine import EligibilityEngine, EligibilityVerdictType, DetailedEligibilityVerdict


def test_qualifies_all_criteria():
    profile = {
        "name": "रामवती",
        "age": 42,
        "gender": "Female",
        "state": "Uttar Pradesh",
        "district": "Barabanki",
        "approx_income_bracket": "below_2_lakh",
        "social_category": "OBC",
        "occupation": "Farmer",
        "disability_status": False
    }
    scheme = {
        "id": 1,
        "name": "Kisan Bio-Energy Scheme",
        "eligibility_criteria": {
            "min_age": 18,
            "max_age": 60,
            "applicable_states": ["Uttar Pradesh"],
            "income_ceiling": 200000,
            "occupation": "Farmer"
        }
    }
    verdict = EligibilityEngine.evaluate_scheme(profile, scheme)
    assert verdict.verdict == EligibilityVerdictType.QUALIFIES
    assert len(verdict.disqualification_reasons) == 0
    assert len(verdict.missing_fields) == 0


def test_disqualified_under_age():
    profile = {"age": 16, "state": "Delhi"}
    scheme = {
        "id": 2,
        "name": "Adult Worker Support",
        "eligibility_criteria": {"min_age": 18}
    }
    verdict = EligibilityEngine.evaluate_scheme(profile, scheme)
    assert verdict.verdict == EligibilityVerdictType.DOES_NOT_QUALIFY
    assert any("न्यूनतम आवश्यक आयु" in r for r in verdict.disqualification_reasons)


def test_disqualified_over_age():
    profile = {"age": 45, "state": "Uttar Pradesh"}
    scheme = {
        "id": 3,
        "name": "Youth Skill Fellowship",
        "eligibility_criteria": {"max_age": 35}
    }
    verdict = EligibilityEngine.evaluate_scheme(profile, scheme)
    assert verdict.verdict == EligibilityVerdictType.DOES_NOT_QUALIFY
    assert any("अधिकतम अनुमत आयु" in r for r in verdict.disqualification_reasons)


def test_disqualified_income_ceiling():
    profile = {"approx_income_bracket": "above_5_lakh"}
    scheme = {
        "id": 4,
        "name": "BPL Subsidy",
        "eligibility_criteria": {"income_ceiling": 200000}
    }
    verdict = EligibilityEngine.evaluate_scheme(profile, scheme)
    assert verdict.verdict == EligibilityVerdictType.DOES_NOT_QUALIFY
    assert any("आय सीमा" in r for r in verdict.disqualification_reasons)


def test_disqualified_social_category():
    profile = {"social_category": "General"}
    scheme = {
        "id": 5,
        "name": "SC/ST Pre-Matric Scholarship",
        "eligibility_criteria": {"social_category": ["SC", "ST"]}
    }
    verdict = EligibilityEngine.evaluate_scheme(profile, scheme)
    assert verdict.verdict == EligibilityVerdictType.DOES_NOT_QUALIFY
    assert any("आरक्षित" in r for r in verdict.disqualification_reasons)


def test_disqualified_state_residence():
    profile = {"state": "Bihar"}
    scheme = {
        "id": 6,
        "name": "Delhi Pension Scheme",
        "eligibility_criteria": {"state_restriction": "Delhi"}
    }
    verdict = EligibilityEngine.evaluate_scheme(profile, scheme)
    assert verdict.verdict == EligibilityVerdictType.DOES_NOT_QUALIFY
    assert any("Delhi के निवासियों के लिए" in r for r in verdict.disqualification_reasons)


def test_disqualified_gender_exclusivity():
    profile = {"gender": "Male"}
    scheme = {
        "id": 7,
        "name": "Mahila Samman Yojana",
        "eligibility_criteria": {"gender": "Female"}
    }
    verdict = EligibilityEngine.evaluate_scheme(profile, scheme)
    assert verdict.verdict == EligibilityVerdictType.DOES_NOT_QUALIFY
    assert any("महिला लाभार्थियों के लिए" in r for r in verdict.disqualification_reasons)


def test_disqualified_disability_mandate():
    profile = {"disability_status": False}
    scheme = {
        "id": 8,
        "name": "Divyangjan Wheelchair Subsidy",
        "eligibility_criteria": {"disability_required": True}
    }
    verdict = EligibilityEngine.evaluate_scheme(profile, scheme)
    assert verdict.verdict == EligibilityVerdictType.DOES_NOT_QUALIFY
    assert any("दिव्यांग" in r for r in verdict.disqualification_reasons)


def test_needs_more_info_when_fields_missing():
    profile = {"name": "अमित"}  # Missing age, state, income
    scheme = {
        "id": 9,
        "name": "State Scholarship",
        "eligibility_criteria": {
            "min_age": 18,
            "state_restriction": "Uttar Pradesh",
            "income_ceiling": 200000
        }
    }
    verdict = EligibilityEngine.evaluate_scheme(profile, scheme)
    assert verdict.verdict == EligibilityVerdictType.NEEDS_MORE_INFO
    assert "age" in verdict.missing_fields
    assert "state" in verdict.missing_fields
    assert "approx_income_bracket" in verdict.missing_fields


def test_evaluate_and_rank_candidates_order():
    profile = {
        "age": 25,
        "gender": "Female",
        "state": "Uttar Pradesh",
        "approx_income_bracket": "below_2_lakh",
        "social_category": "OBC",
        "occupation": "Farmer"
    }
    candidates = [
        # Disqualified
        {"id": 1, "name": "Scheme A (Male only)", "eligibility_criteria": {"gender": "Male"}},
        # Needs More Info
        {"id": 2, "name": "Scheme B (Needs Disability)", "eligibility_criteria": {"disability_required": True}},
        # Qualifies
        {"id": 3, "name": "Scheme C (Farmer UP)", "eligibility_criteria": {"occupation": "Farmer", "applicable_states": ["Uttar Pradesh"]}},
    ]
    ranked = EligibilityEngine.evaluate_and_rank_candidates(profile, candidates)
    assert len(ranked) == 3
    # First must be QUALIFIES (Scheme C)
    assert ranked[0].verdict == EligibilityVerdictType.QUALIFIES
    assert ranked[0].scheme_id == 3
    # Second must be NEEDS_MORE_INFO (Scheme B)
    assert ranked[1].verdict == EligibilityVerdictType.NEEDS_MORE_INFO
    assert ranked[1].scheme_id == 2
    # Last must be DOES_NOT_QUALIFY (Scheme A)
    assert ranked[2].verdict == EligibilityVerdictType.DOES_NOT_QUALIFY
    assert ranked[2].scheme_id == 1
