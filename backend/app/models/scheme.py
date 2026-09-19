from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.core.database import Base


class Scheme(Base):
    """
    SQLAlchemy model representing a government scheme scraped from myScheme.gov.in.
    Stores metadata, rich official text, structured core eligibility criteria in JSONB,
    and fine-print conditions.
    """
    __tablename__ = "schemes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(500), nullable=False, index=True)
    slug = Column(String(200), nullable=True, index=True)

    # Geographic and administrative scope
    government_level = Column(String(50), nullable=False, default="Central", index=True)
    government_name = Column(String(100), nullable=False, default="Central Government", index=True)
    scheme_type = Column(String(100), nullable=False, default="welfare_scheme", index=True)

    # Lifecycle and classification
    beneficiary_type = Column(String(50), nullable=False, default="individual", index=True)
    status = Column(String(50), nullable=False, default="active", index=True)
    scheme_family = Column(String(100), nullable=True, index=True)
    parent_scheme_id = Column(Integer, nullable=True)

    category = Column(String(200), nullable=False, index=True)
    categories = Column(JSONB, nullable=True, default=list)  # Preserves all categories if multi-category

    description = Column(Text, nullable=True)
    ministry = Column(String(500), nullable=True)
    department = Column(String(500), nullable=True)
    implementing_agency = Column(String(500), nullable=True)

    # Structured eligibility criteria stored in JSONB:
    # {
    #   "min_age": int | None,
    #   "max_age": int | None,
    #   "age_notes": str | None,
    #   "income_ceiling": float | None,
    #   "applicable_states": list[str],
    #   "social_category": list[str],
    #   "gender": str | None,
    #   "occupation": str | None,
    #   "disability_status": bool | None,
    #   "state_restriction": str | None,
    #   "residence_requirement": str | None,
    #   "other_conditions_text": str,
    #   "extraction_method": str
    # }
    eligibility_criteria = Column(JSONB, nullable=False, default=dict)
    income_tiers = Column(JSONB, nullable=True, default=list)

    benefits = Column(Text, nullable=True)
    required_documents = Column(JSONB, nullable=True, default=list)  # list of strings or OR-groups
    application_process = Column(Text, nullable=True)
    application_url = Column(String(1000), nullable=True)
    contact_information = Column(Text, nullable=True)

    # Fine-print conditions and official guideline document reference
    guideline_document_url = Column(String(1000), nullable=True)
    fine_print_conditions = Column(JSONB, nullable=True, default=list)  # list of {text, category, verifiable_from_profile}

    # Data quality, audit, and verification signals
    confidence_score = Column(Float, nullable=False, default=1.0)
    extraction_verified = Column(Boolean, nullable=False, default=True)
    review_flags = Column(JSONB, nullable=True, default=list)

    source_url = Column(String(1000), unique=True, nullable=False, index=True)
    source_last_checked = Column(DateTime(timezone=True), nullable=True)
    last_scraped_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Scheme(id={self.id}, name='{self.name}', gov='{self.government_name}', type='{self.scheme_type}')>"
