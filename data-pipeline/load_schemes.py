"""
Database loader and synchronizer script for YojanaVaani Phase 2.
Reads scraped scheme JSON and upserts records into the PostgreSQL `schemes` table.
Ensures database strictly contains Central, Delhi, and UP schemes.
Idempotent: Safe to re-run multiple times without creating duplicate records.
"""

import json
import os
import sys
from datetime import datetime, timezone
import logging

from sqlalchemy import create_engine, select, func, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker

# Add project root and backend to path so backend models can be imported
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.models.scheme import Scheme
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "scraped_schemes.json")
ALLOWED_GOVERNMENTS = ["Central Government", "Delhi Government", "Uttar Pradesh Government"]


def get_db_engine():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        db_url = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@localhost:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    if "@postgres:" in db_url and not os.path.exists("/.dockerenv"):
        db_url = db_url.replace("@postgres:", "@localhost:")
    return create_engine(db_url)


def clean_string_field(val) -> str | None:
    if not val:
        return None
    if isinstance(val, dict):
        return str(val.get("label") or val.get("value") or "")
    return str(val).strip()


def load_schemes(json_path: str = DATA_FILE):
    if not os.path.exists(json_path):
        logger.error(f"Data file not found: {json_path}. Run scrape_schemes.py first!")
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        schemes_data = json.load(f)

    logger.info(f"Loaded {len(schemes_data)} schemes from {json_path}")

    engine = get_db_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    # Filter out any scheme outside allowed jurisdictions
    valid_schemes = [
        s for s in schemes_data if s.get("government_name") in ALLOWED_GOVERNMENTS
    ]
    logger.info(f"Valid Central/Delhi/UP schemes to synchronize: {len(valid_schemes)}")

    valid_urls = set()
    upserted_count = 0

    for item in valid_schemes:
        source_url = item["source_url"]
        valid_urls.add(source_url)

        ministry_str = clean_string_field(item.get("ministry"))
        dept_str = clean_string_field(item.get("department"))
        agency_str = clean_string_field(item.get("implementing_agency"))
        min_or_dept = clean_string_field(item.get("ministry_or_department")) or ministry_str or dept_str

        # Prepare insert statement with PostgreSQL UPSERT (ON CONFLICT DO UPDATE)
        stmt = insert(Scheme).values(
            name=item["name"],
            slug=item.get("slug"),
            government_level=item.get("government_level", "Central"),
            government_name=item.get("government_name", "Central Government"),
            scheme_type=item.get("scheme_type", "welfare_scheme"),
            category=item["category"],
            categories=item.get("categories", [item["category"]]),
            description=item.get("description", ""),
            ministry=ministry_str,
            department=dept_str,
            implementing_agency=agency_str,
            ministry_or_department=min_or_dept,
            benefits=item.get("benefits", ""),
            eligibility_criteria=item.get("eligibility_criteria", {}),
            required_documents=item.get("required_documents", []),
            application_process=item.get("application_process", ""),
            application_url=item.get("application_url"),
            contact_information=item.get("contact_information"),
            guideline_document_url=item.get("guideline_document_url"),
            fine_print_conditions=item.get("fine_print_conditions", []),
            source_url=source_url,
            source_last_checked=datetime.now(timezone.utc),
            last_scraped_at=datetime.now(timezone.utc),
        )

        # On conflict update all non-key fields
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["source_url"],
            set_={
                "name": stmt.excluded.name,
                "slug": stmt.excluded.slug,
                "government_level": stmt.excluded.government_level,
                "government_name": stmt.excluded.government_name,
                "scheme_type": stmt.excluded.scheme_type,
                "category": stmt.excluded.category,
                "categories": stmt.excluded.categories,
                "description": stmt.excluded.description,
                "ministry": stmt.excluded.ministry,
                "department": stmt.excluded.department,
                "implementing_agency": stmt.excluded.implementing_agency,
                "ministry_or_department": stmt.excluded.ministry_or_department,
                "benefits": stmt.excluded.benefits,
                "eligibility_criteria": stmt.excluded.eligibility_criteria,
                "required_documents": stmt.excluded.required_documents,
                "application_process": stmt.excluded.application_process,
                "application_url": stmt.excluded.application_url,
                "contact_information": stmt.excluded.contact_information,
                "guideline_document_url": stmt.excluded.guideline_document_url,
                "fine_print_conditions": stmt.excluded.fine_print_conditions,
                "source_last_checked": stmt.excluded.source_last_checked,
                "last_scraped_at": stmt.excluded.last_scraped_at,
            },
        )

        session.execute(upsert_stmt)
        upserted_count += 1

    session.commit()
    logger.info(f"Upserted {upserted_count} valid schemes successfully.")

    # Clean synchronization: Purge out-of-scope state schemes or records not in valid dataset
    logger.info("Synchronizing database: purging out-of-scope state records...")
    purge_stmt = delete(Scheme).where(
        (Scheme.government_name.not_in(ALLOWED_GOVERNMENTS)) |
        (Scheme.source_url.not_in(valid_urls))
    )
    purge_result = session.execute(purge_stmt)
    session.commit()
    logger.info(f"Purged {purge_result.rowcount} out-of-scope / stale records from database.")

    total_in_db = session.scalar(select(func.count(Scheme.id)))
    session.close()

    logger.info(f"Total verified schemes currently in 'schemes' table: {total_in_db}")


if __name__ == "__main__":
    load_schemes()
