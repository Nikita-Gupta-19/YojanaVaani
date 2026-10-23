"""
Deterministic Eligibility Matching Engine (Phase 6).

CRITICAL NON-NEGOTIABLE ARCHITECTURAL RULE:
This module contains 100% plain, deterministic Python logic.
NO language model (LLM), neural approximation, or probabilistic heuristic
is permitted to decide a citizen's statutory eligibility.
All verdicts are auditable, verifiable, and explainable with concrete statutory reasons.

Evaluates:
- Age limits (min_age, max_age)
- Income brackets and ceiling amounts (income_ceiling, approx_income_bracket)
- Social reservation categories (social_category: General, OBC, SC, ST)
- Applicable states & geographic residency restrictions
- Gender eligibility (Female, Male, Transgender, All)
- Occupational requirements (Farmer, Student, Laborer, Homemaker, etc.)
- Disability criteria (disability_status)
- Fine-print other_conditions (flagged transparently as "needs manual review")
"""

from enum import Enum
import logging
from typing import Any, Dict, List, Optional, Set, Union
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EligibilityVerdictType(str, Enum):
    """Controlled verdict outcomes according to Phase 6 specifications."""
    QUALIFIES = "QUALIFIES"
    NEEDS_MORE_INFO = "NEEDS_MORE_INFO"
    DOES_NOT_QUALIFY = "DOES_NOT_QUALIFY"


class RuleEvaluationDetail(BaseModel):
    """Fine-grained audit trail for an individual criterion evaluation."""
    criterion_name: str = Field(..., description="Name of the criterion (e.g. age, income, state)")
    status: EligibilityVerdictType = Field(..., description="Outcome for this specific criterion")
    expected_rule: str = Field(..., description="Statutory requirement description")
    citizen_value: Any = Field(default=None, description="Citizen's profile value for this criterion")
    message: str = Field(..., description="Auditable explanation in Hindi/English")


class DetailedEligibilityVerdict(BaseModel):
    """
    Structured, auditable eligibility decision returned for a specific welfare scheme.
    """
    scheme_id: int = Field(..., description="Scheme primary key")
    scheme_name: str = Field(..., description="Official scheme name")
    verdict: EligibilityVerdictType = Field(..., description="Overall qualification verdict")
    overall_reason: str = Field(..., description="Human-readable summary of verdict")
    disqualification_reasons: List[str] = Field(default_factory=list, description="Specific disqualifying statutory violations")
    missing_fields: List[str] = Field(default_factory=list, description="Demographic fields missing from profile")
    manual_review_flags: List[str] = Field(default_factory=list, description="Fine-print clauses flagged for manual officer check")
    rule_details: List[RuleEvaluationDetail] = Field(default_factory=list, description="Step-by-step audit trail")


class EligibilityEngine:
    """
    Rule-based deterministic eligibility evaluation engine.
    """

    @staticmethod
    def evaluate_scheme(profile: Dict[str, Any], scheme: Union[Dict[str, Any], Any]) -> DetailedEligibilityVerdict:
        """
        Deterministically evaluates a citizen profile against a single scheme's criteria.

        Args:
            profile: Citizen demographic dictionary (from CitizenProfile or baseline interview).
            scheme: Scheme dictionary or SQLAlchemy Scheme model.

        Returns:
            DetailedEligibilityVerdict with auditable justification.
        """
        # Support both SQLAlchemy model and dictionary representation
        if hasattr(scheme, "__dict__") and not isinstance(scheme, dict):
            s_id = getattr(scheme, "id", 0)
            s_name = getattr(scheme, "name", "Unknown Scheme")
            criteria = getattr(scheme, "eligibility_criteria", {}) or {}
        else:
            s_id = scheme.get("id", 0)
            s_name = scheme.get("name", "Unknown Scheme")
            criteria = scheme.get("eligibility_criteria", {}) or {}

        # If criteria is a string (rare legacy case), safeguard it
        if not isinstance(criteria, dict):
            criteria = {}

        rule_details: List[RuleEvaluationDetail] = []
        disqualifications: List[str] = []
        missing_fields: List[str] = []
        manual_flags: List[str] = []

        # ---------------------------------------------------------------------
        # 1. AGE CHECK (min_age, max_age)
        # ---------------------------------------------------------------------
        min_age = criteria.get("min_age")
        max_age = criteria.get("max_age")
        citizen_age = profile.get("age")

        if min_age is not None or max_age is not None:
            rule_desc = f"आयु सीमा: {min_age or 0} से {max_age or 'असीमित'} वर्ष"
            if citizen_age is None:
                missing_fields.append("age")
                rule_details.append(RuleEvaluationDetail(
                    criterion_name="age",
                    status=EligibilityVerdictType.NEEDS_MORE_INFO,
                    expected_rule=rule_desc,
                    citizen_value=None,
                    message="नागरिक की आयु का विवरण अनुपलब्ध है (Age is missing)."
                ))
            elif min_age is not None and citizen_age < min_age:
                reason = f"नागरिक की आयु ({citizen_age} वर्ष) न्यूनतम आवश्यक आयु ({min_age} वर्ष) से कम है (Citizen age is below minimum required age of {min_age} years)."
                disqualifications.append(reason)
                rule_details.append(RuleEvaluationDetail(
                    criterion_name="age",
                    status=EligibilityVerdictType.DOES_NOT_QUALIFY,
                    expected_rule=rule_desc,
                    citizen_value=citizen_age,
                    message=reason
                ))
            elif max_age is not None and citizen_age > max_age:
                reason = f"नागरिक की आयु ({citizen_age} वर्ष) अधिकतम अनुमत आयु ({max_age} वर्ष) से अधिक है (Citizen age exceeds maximum permissible age of {max_age} years)."
                disqualifications.append(reason)
                rule_details.append(RuleEvaluationDetail(
                    criterion_name="age",
                    status=EligibilityVerdictType.DOES_NOT_QUALIFY,
                    expected_rule=rule_desc,
                    citizen_value=citizen_age,
                    message=reason
                ))
            else:
                rule_details.append(RuleEvaluationDetail(
                    criterion_name="age",
                    status=EligibilityVerdictType.QUALIFIES,
                    expected_rule=rule_desc,
                    citizen_value=citizen_age,
                    message=f"आयु ({citizen_age} वर्ष) निर्धारित सीमा के अंतर्गत है।"
                ))

        # ---------------------------------------------------------------------
        # 2. INCOME CHECK (income_ceiling, approx_income_bracket)
        # ---------------------------------------------------------------------
        ceiling = criteria.get("income_ceiling")
        citizen_income_bracket = profile.get("approx_income_bracket")

        if ceiling is not None and ceiling > 0:
            rule_desc = f"वार्षिक पारिवारिक आय अधिकतम ₹{ceiling:,.0f}"
            if citizen_income_bracket is None:
                missing_fields.append("approx_income_bracket")
                rule_details.append(RuleEvaluationDetail(
                    criterion_name="income",
                    status=EligibilityVerdictType.NEEDS_MORE_INFO,
                    expected_rule=rule_desc,
                    citizen_value=None,
                    message="आय श्रेणी (Income Bracket) का विवरण अनुपलब्ध है।"
                ))
            else:
                # Deterministic bracket bounds mapping:
                # "below_2_lakh" -> [0, 200,000]
                # "2_to_5_lakh"  -> (200,000, 500,000]
                # "above_5_lakh" -> > 500,000
                disqualified = False
                if ceiling <= 200000:
                    if citizen_income_bracket in ["2_to_5_lakh", "above_5_lakh"]:
                        disqualified = True
                elif ceiling <= 500000:
                    if citizen_income_bracket == "above_5_lakh":
                        disqualified = True

                if disqualified:
                    reason = f"वार्षिक आय सीमा (₹{ceiling:,.0f}) से अधिक है (वर्तमान श्रेणी: {citizen_income_bracket})।"
                    disqualifications.append(reason)
                    rule_details.append(RuleEvaluationDetail(
                        criterion_name="income",
                        status=EligibilityVerdictType.DOES_NOT_QUALIFY,
                        expected_rule=rule_desc,
                        citizen_value=citizen_income_bracket,
                        message=reason
                    ))
                else:
                    rule_details.append(RuleEvaluationDetail(
                        criterion_name="income",
                        status=EligibilityVerdictType.QUALIFIES,
                        expected_rule=rule_desc,
                        citizen_value=citizen_income_bracket,
                        message="आय सीमा निर्धारित आय सीमा के अनुकूल है।"
                    ))

        # ---------------------------------------------------------------------
        # 3. SOCIAL RESERVATION CATEGORY (social_category)
        # ---------------------------------------------------------------------
        allowed_cats_raw = criteria.get("social_category")
        allowed_cats: Set[str] = set()
        if isinstance(allowed_cats_raw, list):
            allowed_cats = {c.strip().lower() for c in allowed_cats_raw if isinstance(c, str)}
        elif isinstance(allowed_cats_raw, str) and allowed_cats_raw.strip():
            allowed_cats = {allowed_cats_raw.strip().lower()}

        # Filter out generic wildcards like "all", "general", "any"
        is_restricted_cat = bool(allowed_cats and not any(w in allowed_cats for w in ["all", "any", "general"]))

        if is_restricted_cat:
            rule_desc = f"आरक्षित वर्ग: {', '.join(sorted(c.upper() for c in allowed_cats))}"
            citizen_cat = profile.get("social_category")
            if not citizen_cat:
                missing_fields.append("social_category")
                rule_details.append(RuleEvaluationDetail(
                    criterion_name="social_category",
                    status=EligibilityVerdictType.NEEDS_MORE_INFO,
                    expected_rule=rule_desc,
                    citizen_value=None,
                    message="सामाजिक वर्ग (Social Category) की जानकारी आवश्यक है।"
                ))
            else:
                cat_lower = citizen_cat.strip().lower()
                # Check matching (e.g. "sc", "st", "obc")
                if cat_lower not in allowed_cats and not any(allowed in cat_lower for allowed in allowed_cats):
                    reason = f"यह योजना विशेष रूप से {', '.join(sorted(c.upper() for c in allowed_cats))} वर्ग के लिए आरक्षित है; नागरिक वर्ग: {citizen_cat}।"
                    disqualifications.append(reason)
                    rule_details.append(RuleEvaluationDetail(
                        criterion_name="social_category",
                        status=EligibilityVerdictType.DOES_NOT_QUALIFY,
                        expected_rule=rule_desc,
                        citizen_value=citizen_cat,
                        message=reason
                    ))
                else:
                    rule_details.append(RuleEvaluationDetail(
                        criterion_name="social_category",
                        status=EligibilityVerdictType.QUALIFIES,
                        expected_rule=rule_desc,
                        citizen_value=citizen_cat,
                        message=f"सामाजिक वर्ग ({citizen_cat}) योजना पात्रता के अनुकूल है।"
                    ))

        # ---------------------------------------------------------------------
        # 4. STATE RESTRICTION / RESIDENCE REQUIREMENT
        # ---------------------------------------------------------------------
        state_rest = criteria.get("state_restriction") or ""
        app_states = criteria.get("applicable_states") or []
        if isinstance(app_states, str):
            app_states = [app_states]

        # Combine all explicit geographic restrictions
        geo_restrictions = [s.strip() for s in app_states if s and s.strip().lower() not in ["all", "central", "all-india", "pan-india", "national"]]
        if state_rest and state_rest.strip().lower() not in ["all", "central", "all-india", "pan-india", "national"]:
            geo_restrictions.append(state_rest.strip())

        if geo_restrictions:
            rule_desc = f"राज्य प्रतिबंध: {', '.join(set(geo_restrictions))}"
            citizen_state = profile.get("state")
            if not citizen_state:
                missing_fields.append("state")
                rule_details.append(RuleEvaluationDetail(
                    criterion_name="state",
                    status=EligibilityVerdictType.NEEDS_MORE_INFO,
                    expected_rule=rule_desc,
                    citizen_value=None,
                    message="नागरिक के राज्य का विवरण अनुपलब्ध है।"
                ))
            else:
                cit_state_lower = citizen_state.lower().strip()
                match = any(
                    res.lower() in cit_state_lower or cit_state_lower in res.lower()
                    for res in geo_restrictions
                )
                if not match:
                    reason = f"यह योजना केवल {', '.join(set(geo_restrictions))} के निवासियों के लिए है; नागरिक का राज्य: {citizen_state}।"
                    disqualifications.append(reason)
                    rule_details.append(RuleEvaluationDetail(
                        criterion_name="state",
                        status=EligibilityVerdictType.DOES_NOT_QUALIFY,
                        expected_rule=rule_desc,
                        citizen_value=citizen_state,
                        message=reason
                    ))
                else:
                    rule_details.append(RuleEvaluationDetail(
                        criterion_name="state",
                        status=EligibilityVerdictType.QUALIFIES,
                        expected_rule=rule_desc,
                        citizen_value=citizen_state,
                        message=f"नागरिक का राज्य ({citizen_state}) योजना के अंतर्गत आता है।"
                    ))

        # ---------------------------------------------------------------------
        # 5. GENDER CHECK
        # ---------------------------------------------------------------------
        req_gender = criteria.get("gender")
        if req_gender and isinstance(req_gender, str):
            g_clean = req_gender.strip().lower()
            if g_clean not in ["all", "any", "both"]:
                rule_desc = f"लिंग पात्रता: {req_gender.capitalize()}"
                citizen_gender = profile.get("gender")
                if not citizen_gender:
                    missing_fields.append("gender")
                    rule_details.append(RuleEvaluationDetail(
                        criterion_name="gender",
                        status=EligibilityVerdictType.NEEDS_MORE_INFO,
                        expected_rule=rule_desc,
                        citizen_value=None,
                        message="लिंग विवरण अनुपलब्ध है।"
                    ))
                else:
                    c_gen_clean = citizen_gender.strip().lower()
                    is_c_female = ("female" in c_gen_clean or "महिला" in c_gen_clean or "स्त्री" in c_gen_clean)
                    is_c_male = ("पुरुष" in c_gen_clean or (c_gen_clean in ["male", "m"] or c_gen_clean.startswith("male"))) and not is_c_female

                    is_req_female = ("female" in g_clean or "महिला" in g_clean or "स्त्री" in g_clean)
                    is_req_male = ("पुरुष" in g_clean or (g_clean in ["male", "m"] or g_clean.startswith("male"))) and not is_req_female

                    if is_req_female and not is_c_female:
                        reason = "यह योजना विशेष रूप से महिला लाभार्थियों के लिए है।"
                        disqualifications.append(reason)
                        rule_details.append(RuleEvaluationDetail(
                            criterion_name="gender",
                            status=EligibilityVerdictType.DOES_NOT_QUALIFY,
                            expected_rule=rule_desc,
                            citizen_value=citizen_gender,
                            message=reason
                        ))
                    elif is_req_male and not is_c_male:
                        reason = "यह योजना विशेष रूप से पुरुष लाभार्थियों के लिए है।"
                        disqualifications.append(reason)
                        rule_details.append(RuleEvaluationDetail(
                            criterion_name="gender",
                            status=EligibilityVerdictType.DOES_NOT_QUALIFY,
                            expected_rule=rule_desc,
                            citizen_value=citizen_gender,
                            message=reason
                        ))
                    else:
                        rule_details.append(RuleEvaluationDetail(
                            criterion_name="gender",
                            status=EligibilityVerdictType.QUALIFIES,
                            expected_rule=rule_desc,
                            citizen_value=citizen_gender,
                            message=f"लिंग ({citizen_gender}) योजना पात्रता के अनुकूल है।"
                        ))

        # ---------------------------------------------------------------------
        # 6. OCCUPATION CHECK
        # ---------------------------------------------------------------------
        req_occ = criteria.get("occupation")
        if req_occ and isinstance(req_occ, str) and req_occ.strip().lower() not in ["all", "any"]:
            rule_desc = f"व्यवसाय पात्रता: {req_occ}"
            citizen_occ = profile.get("occupation")
            if not citizen_occ:
                missing_fields.append("occupation")
                rule_details.append(RuleEvaluationDetail(
                    criterion_name="occupation",
                    status=EligibilityVerdictType.NEEDS_MORE_INFO,
                    expected_rule=rule_desc,
                    citizen_value=None,
                    message="नागरिक के व्यवसाय (Occupation) का विवरण अनुपलब्ध है।"
                ))
            else:
                c_occ_lower = citizen_occ.lower()
                r_occ_lower = req_occ.lower()

                # Specific check for farmer / kisan schemes
                farmer_terms = ["farmer", "किसान", "खेती", "कृषि", "कृषक", "agriculture"]
                is_farmer_scheme = any(t in r_occ_lower for t in farmer_terms)
                is_citizen_farmer = any(t in c_occ_lower for t in farmer_terms)

                if is_farmer_scheme and not is_citizen_farmer:
                    reason = f"यह योजना किसानों के लिए है; नागरिक का व्यवसाय: {citizen_occ}।"
                    disqualifications.append(reason)
                    rule_details.append(RuleEvaluationDetail(
                        criterion_name="occupation",
                        status=EligibilityVerdictType.DOES_NOT_QUALIFY,
                        expected_rule=rule_desc,
                        citizen_value=citizen_occ,
                        message=reason
                    ))
                elif not is_farmer_scheme and r_occ_lower not in c_occ_lower and c_occ_lower not in r_occ_lower:
                    reason = f"यह योजना {req_occ} वर्ग के लिए लक्षित है; नागरिक का व्यवसाय: {citizen_occ}।"
                    disqualifications.append(reason)
                    rule_details.append(RuleEvaluationDetail(
                        criterion_name="occupation",
                        status=EligibilityVerdictType.DOES_NOT_QUALIFY,
                        expected_rule=rule_desc,
                        citizen_value=citizen_occ,
                        message=reason
                    ))
                else:
                    rule_details.append(RuleEvaluationDetail(
                        criterion_name="occupation",
                        status=EligibilityVerdictType.QUALIFIES,
                        expected_rule=rule_desc,
                        citizen_value=citizen_occ,
                        message=f"व्यवसाय ({citizen_occ}) योजना की शर्तों के अनुकूल है।"
                    ))

        # ---------------------------------------------------------------------
        # 7. DISABILITY STATUS
        # ---------------------------------------------------------------------
        dis_req = criteria.get("disability_status")
        if dis_req is None:
            dis_req = criteria.get("disability_required")

        if dis_req is True:
            rule_desc = "दिव्यांगता अनिवार्यता: हाँ (40% या अधिक दिव्यांगता)"
            citizen_dis = profile.get("disability_status")
            if citizen_dis is None:
                missing_fields.append("disability_status")
                rule_details.append(RuleEvaluationDetail(
                    criterion_name="disability_status",
                    status=EligibilityVerdictType.NEEDS_MORE_INFO,
                    expected_rule=rule_desc,
                    citizen_value=None,
                    message="दिव्यांगता प्रमाण का विवरण आवश्यक है।"
                ))
            elif citizen_dis is False:
                reason = "यह योजना विशेष रूप से दिव्यांग (Divyangjan) नागरिकों के लिए है।"
                disqualifications.append(reason)
                rule_details.append(RuleEvaluationDetail(
                    criterion_name="disability_status",
                    status=EligibilityVerdictType.DOES_NOT_QUALIFY,
                    expected_rule=rule_desc,
                    citizen_value=False,
                    message=reason
                ))
            else:
                rule_details.append(RuleEvaluationDetail(
                    criterion_name="disability_status",
                    status=EligibilityVerdictType.QUALIFIES,
                    expected_rule=rule_desc,
                    citizen_value=True,
                    message="दिव्यांगता मानदंड सत्यापित है।"
                ))

        # ---------------------------------------------------------------------
        # 8. FREE-TEXT OTHER CONDITIONS (Manual Review Flags)
        # ---------------------------------------------------------------------
        # NOTE ON FREE-TEXT CONDITIONS:
        # Complex statutory clauses (e.g. "Land holding under 2 hectares", "Must not own a four-wheeler",
        # "Must be a single earning member") cannot be reliably extracted using naive regular expressions
        # without introducing false-positive disqualifications. We deliberately and honestly flag
        # these clauses as "needs manual review" to be confirmed during physical verification or
        # document review, adhering strictly to auditable rule engineering.
        other_cond = criteria.get("other_conditions_text") or criteria.get("other_conditions")
        if other_cond and isinstance(other_cond, str) and len(other_cond.strip()) > 10:
            flag_text = f"अतिरिक्त शर्त (मैनुअल समीक्षा): {other_cond.strip()[:150]}..."
            manual_flags.append(flag_text)

        # ---------------------------------------------------------------------
        # 9. FINAL VERDICT SYNTHESIS
        # ---------------------------------------------------------------------
        if disqualifications:
            final_verdict = EligibilityVerdictType.DOES_NOT_QUALIFY
            overall_reason = "; ".join(disqualifications)
        elif missing_fields:
            final_verdict = EligibilityVerdictType.NEEDS_MORE_INFO
            overall_reason = f"पात्रता की पुष्टि के लिए अतिरिक्त विवरण आवश्यक हैं: {', '.join(missing_fields)}"
        else:
            final_verdict = EligibilityVerdictType.QUALIFIES
            overall_reason = "नागरिक सभी निर्धारित पात्रता शर्तों को पूरा करते हैं।"

        return DetailedEligibilityVerdict(
            scheme_id=s_id,
            scheme_name=s_name,
            verdict=final_verdict,
            overall_reason=overall_reason,
            disqualification_reasons=disqualifications,
            missing_fields=missing_fields,
            manual_review_flags=manual_flags,
            rule_details=rule_details
        )

    @classmethod
    def evaluate_and_rank_candidates(
        cls,
        profile: Dict[str, Any],
        candidate_schemes: List[Dict[str, Any]]
    ) -> List[DetailedEligibilityVerdict]:
        """
        Evaluates a list of candidate schemes against a citizen profile and
        returns them ranked deterministically:
        1. QUALIFIES first
        2. NEEDS_MORE_INFO second
        3. DOES_NOT_QUALIFY last
        Within each bucket, candidate order (relevance score) is preserved.
        """
        verdicts: List[DetailedEligibilityVerdict] = []
        for scheme in candidate_schemes:
            verdict = cls.evaluate_scheme(profile, scheme)
            verdicts.append(verdict)

        # Sort order rank: QUALIFIES (0) -> NEEDS_MORE_INFO (1) -> DOES_NOT_QUALIFY (2)
        rank_order = {
            EligibilityVerdictType.QUALIFIES: 0,
            EligibilityVerdictType.NEEDS_MORE_INFO: 1,
            EligibilityVerdictType.DOES_NOT_QUALIFY: 2,
        }

        verdicts.sort(key=lambda v: rank_order.get(v.verdict, 3))
        return verdicts
