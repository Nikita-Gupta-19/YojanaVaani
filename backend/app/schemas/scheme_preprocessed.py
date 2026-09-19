"""
Revised Pydantic Schema for YojanaVaani Preprocessed Government Schemes.

Reflects clean structured fields, confidence scoring, life-cycle tracking,
canonical taxonomy, tiered income slabs, and structured benefit amounts
prior to the Phase 3 eligibility-matching engine.
"""

from enum import Enum
from typing import List, Literal, Optional, Union
from pydantic import BaseModel, Field


class BeneficiaryType(str, Enum):
    """Target beneficiary classification to filter citizen vs institutional schemes."""
    individual = "individual"
    household = "household"
    enterprise = "enterprise"
    institution = "institution"
    award = "award"
    service = "service"


class LifecycleStatus(str, Enum):
    """Operational status of the government scheme."""
    active = "active"
    closed = "closed"
    lapsed = "lapsed"
    outdated_rates = "outdated_rates"
    under_review = "under_review"


class BenefitType(str, Enum):
    """Type of financial, material, or service benefit provided."""
    fixed = "fixed"
    percentage = "percentage"
    tiered = "tiered"
    reimbursement = "reimbursement"
    subsidy = "subsidy"
    in_kind = "in_kind"
    pension = "pension"
    loan = "loan"
    scholarship = "scholarship"
    unstructured = "unstructured"


class Gender(str, Enum):
    """Controlled gender vocabulary."""
    ALL = "All"
    FEMALE = "Female"
    MALE = "Male"
    TRANSGENDER = "Transgender"


class SocialCategory(str, Enum):
    """Controlled caste/social reservation categories (BPL is moved to economic)."""
    ALL = "All"
    GENERAL = "General"
    SC = "SC"
    ST = "ST"
    OBC = "OBC"
    MINORITY = "Minority"
    EWS = "EWS"


class IncomeTier(BaseModel):
    """Represents slab-based/tiered income limits with corresponding benefit values."""
    tier_name: Optional[str] = None
    min_income: Optional[float] = Field(default=None, description="Minimum annual income in INR (inclusive)")
    max_income: Optional[float] = Field(default=None, description="Maximum annual income in INR (inclusive)")
    benefit_value: Union[float, str] = Field(description="Benefit percentage, amount, or formula")
    benefit_type: str = Field(default="subsidy", description="e.g. percentage, fixed_amount, fee_waiver")
    notes: Optional[str] = None


class StructuredBenefit(BaseModel):
    """Structured extraction of scheme financial and in-kind benefits."""
    benefit_min: Optional[float] = Field(default=None, description="Minimum monetary benefit amount in INR")
    benefit_max: Optional[float] = Field(default=None, description="Maximum monetary benefit amount in INR")
    benefit_type: BenefitType = Field(default=BenefitType.unstructured)
    unit: Optional[str] = Field(default="INR", description="e.g. INR, percentage, kg, kWh")
    frequency: Optional[str] = Field(default=None, description="one-time, per_month, per_year, per_installment")
    benefit_condition: Optional[str] = Field(default=None, description="e.g. 'whichever is less', 'up to 2 children'")
    income_tiers: List[IncomeTier] = Field(default_factory=list, description="Populated for slab-based schemes")
    raw_text: str = Field(default="", description="Cleaned prose of benefits")


class DocumentRequirement(BaseModel):
    """Document requirement with OR-grouping support."""
    purpose: str = Field(description="Purpose: identity_proof, income_proof, residence_proof, category_proof, etc.")
    accepts: List[str] = Field(description="List of documents that satisfy this requirement (OR-group)")
    required: bool = True
    notes: Optional[str] = None


class FinePrintRule(BaseModel):
    """Specific fine-print restriction, exclusion, or procedure."""
    text: str = Field(description="Clean condition text")
    category: Literal["exclusion", "documentation", "procedural", "quota", "combination_restriction"]
    verifiable_from_profile: bool = Field(default=False, description="True if checkable from Stage 1 interview")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class CleanedEligibility(BaseModel):
    """Audited, normalized, and validated eligibility rules."""
    min_age: Optional[int] = Field(default=None, ge=0, le=120)
    max_age: Optional[int] = Field(default=None, ge=0, le=120)
    age_notes: Optional[str] = None
    income_ceiling: Optional[float] = Field(default=None, description="Scalar annual income ceiling in INR")
    bpl_required: bool = Field(default=False, description="True if BPL / Antyodaya / Ration card is mandatory")
    income_tiers: List[IncomeTier] = Field(default_factory=list)
    gender: Gender = Field(default=Gender.ALL)
    social_categories: List[SocialCategory] = Field(default_factory=lambda: [SocialCategory.ALL])
    occupations: List[str] = Field(default_factory=lambda: ["All"], description="Canonical occupation list")
    disability_required: Optional[bool] = None
    min_disability_percentage: Optional[int] = Field(default=None, ge=0, le=100)
    state_restriction: Optional[str] = None
    residence_requirement: Optional[str] = None
    other_conditions_text: str = Field(default="", description="Source of truth full official eligibility text")
    extraction_method: str = Field(default="verified_rules_engine")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    confidence_components: Optional[dict] = Field(default=None, description="Detailed component weights: age, income, gender, category")


class SchemePreprocessed(BaseModel):
    """Complete preprocessed government scheme record ready for Phase 3 matching."""
    id: int
    name: str
    slug: Optional[str] = None
    government_level: Literal["Central", "State"]
    government_name: Literal["Central Government", "Delhi Government", "Uttar Pradesh Government"]
    category: str
    categories: List[str] = Field(default_factory=list)
    scheme_type: str
    beneficiary_type: BeneficiaryType = Field(default=BeneficiaryType.individual)
    status: LifecycleStatus = Field(default=LifecycleStatus.active)
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    parent_scheme_id: Optional[int] = None
    scheme_family: Optional[str] = None
    ministry: Optional[str] = None
    department: Optional[str] = None
    implementing_agency: Optional[str] = None
    description: str = ""
    eligibility: CleanedEligibility
    benefits: StructuredBenefit
    required_documents: List[DocumentRequirement] = Field(default_factory=list)
    fine_print_conditions: List[FinePrintRule] = Field(default_factory=list)
    application_process: str = ""
    application_url: Optional[str] = None
    guideline_document_url: Optional[str] = None
    source_url: str
    last_scraped_at: str
    source_last_checked: Optional[str] = None
    scheme_last_verified: Optional[str] = None
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    extraction_verified: bool = Field(default=True)
    review_flags: List[str] = Field(default_factory=list)
