"""
Conversation state and citizen profile models for YojanaVaani (Phase 3).

Defines the structured representations for:
- CitizenProfile: Demographic and economic attributes collected during baseline interview.
- ConversationTurn: Single dialogue turn in conversation history.
- ConversationStatus: Explicit lifecycle status across Stage 1 (baseline) and Stage 2 (agentic RAG).
- ConversationState: Complete runtime state passed between stages and MCP tools.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class ConversationStatus(str, Enum):
    """Lifecycle status of the conversational session."""
    baseline_interview = "baseline_interview"
    scheme_matching = "scheme_matching"
    awaiting_document = "awaiting_document"
    results_ready = "results_ready"
    escalated = "escalated"


class IncomeBracket(str, Enum):
    """Standardized income brackets for verbal communication."""
    BELOW_2_LAKH = "below_2_lakh"      # < ₹2,00,000 / year
    BETWEEN_2_AND_5_LAKH = "2_to_5_lakh"  # ₹2,00,000 - ₹5,00,000 / year
    ABOVE_5_LAKH = "above_5_lakh"      # > ₹5,00,000 / year


class SocialCategoryEnum(str, Enum):
    """Controlled social reservation categories."""
    GENERAL = "General"
    OBC = "OBC"
    SC = "SC"
    ST = "ST"
    OTHER = "Other"


class GenderEnum(str, Enum):
    """Controlled gender vocabulary."""
    FEMALE = "Female"
    MALE = "Male"
    TRANSGENDER = "Transgender"
    OTHER = "Other"


class CitizenProfile(BaseModel):
    """
    Structured profile of a citizen, populated incrementally
    during Stage 1 (Baseline Interview) and verified/augmented via OCR in Stage 2.
    """
    name: Optional[str] = Field(default=None, description="Citizen's full name")
    age: Optional[int] = Field(default=None, description="Age in completed years")
    gender: Optional[str] = Field(default=None, description="Gender (Female, Male, Transgender, Other)")
    state: Optional[str] = Field(default=None, description="State of permanent residence")
    district: Optional[str] = Field(default=None, description="District of residence")
    approx_income_bracket: Optional[str] = Field(
        default=None,
        description="Annual household income tier: below_2_lakh, 2_to_5_lakh, or above_5_lakh"
    )
    social_category: Optional[str] = Field(
        default=None,
        description="Statutory social reservation category (General, OBC, SC, ST)"
    )
    occupation: Optional[str] = Field(
        default=None,
        description="Primary occupation (Farmer, Daily Wage, Student, Self-Employed, etc.)"
    )
    disability_status: Optional[bool] = Field(
        default=None,
        description="Whether citizen or household member has a recognized disability"
    )

    def is_complete(self) -> bool:
        """Returns True if all required baseline demographic fields are populated."""
        return all([
            self.name is not None,
            self.age is not None,
            self.gender is not None,
            self.state is not None,
            self.approx_income_bracket is not None,
            self.social_category is not None,
            self.occupation is not None,
            self.disability_status is not None,
        ])


class ConversationTurn(BaseModel):
    """Single conversational turn between assistant, citizen, or system."""
    speaker: str = Field(..., description="Speaker identifier ('assistant', 'citizen', or 'system')")
    text: str = Field(..., description="Verbatim utterance or spoken message")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp"
    )


class ConversationState(BaseModel):
    """
    Master conversation state object.
    Tracks progression through Stage 1 baseline interview and holds context
    for Stage 2 LangGraph agentic reasoning.
    """
    conversation_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Globally unique session identifier"
    )
    citizen_profile: CitizenProfile = Field(
        default_factory=CitizenProfile,
        description="Demographic profile built from interview answers"
    )
    stated_need: Optional[str] = Field(
        default=None,
        description="Open-ended statement of what assistance the citizen seeks"
    )
    baseline_complete: bool = Field(
        default=False,
        description="True once all 9 fixed baseline questions have been answered"
    )
    collected_documents: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of document capture/OCR verification records (populated in Phase 6)"
    )
    conversation_history: List[ConversationTurn] = Field(
        default_factory=list,
        description="Sequential transcript of all dialogue turns"
    )
    candidate_schemes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Retrieved scheme candidates from vector search (populated in Phase 5)"
    )
    missing_facts: List[str] = Field(
        default_factory=list,
        description="Fields required by candidate schemes but missing from profile (Phase 5)"
    )
    status: ConversationStatus = Field(
        default=ConversationStatus.baseline_interview,
        description="Current conversational state machine phase"
    )
    current_question_index: int = Field(
        default=0,
        description="Zero-indexed pointer to the current baseline interview question"
    )
