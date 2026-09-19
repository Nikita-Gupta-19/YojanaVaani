"""
Embedding and indexing script for YojanaVaani Phase 2.
Loads verified Central, Delhi, and UP schemes from PostgreSQL, generates multilingual sentence
embeddings using paraphrase-multilingual-mpnet-base-v2, and indexes them into Chroma DB.
Safely re-runnable: Rebuilds collection idempotently.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
import chromadb
from sentence_transformers import SentenceTransformer

# Add project root and backend to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.models.scheme import Scheme
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CHROMA_DIR = os.path.join(PROJECT_ROOT, "data-pipeline", "chroma_db")
COLLECTION_NAME = "yojana_schemes"
MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"


def get_db_engine():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        db_url = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@localhost:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    if "@postgres:" in db_url and not os.path.exists("/.dockerenv"):
        db_url = db_url.replace("@postgres:", "@localhost:")
    return create_engine(db_url)


def build_index():
    logger.info("Connecting to database to retrieve schemes...")
    engine = get_db_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    schemes = session.scalars(select(Scheme).order_by(Scheme.id)).all()
    session.close()

    if not schemes:
        logger.error("No schemes found in database. Run load_schemes.py first!")
        sys.exit(1)

    logger.info(f"Retrieved {len(schemes)} schemes from PostgreSQL.")

    logger.info(f"Loading embedding model: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)

    documents = []
    metadatas = []
    ids = []

    for s in schemes:
        eligibility_data = s.eligibility_criteria or {}
        other_cond = eligibility_data.get("other_conditions_text", "")
        soc_cat = ", ".join(eligibility_data.get("social_category", []))
        states = ", ".join(eligibility_data.get("applicable_states", []))
        gender = eligibility_data.get("gender") or "All"
        occupation = eligibility_data.get("occupation") or "Any"

        eligibility_summary = (
            f"Government: {s.government_name}; Level: {s.government_level}; "
            f"States: {states}; Gender: {gender}; Occupation: {occupation}; "
            f"Social Category: {soc_cat}; Conditions: {other_cond}"
        )

        # Format fine-print conditions
        fp_conditions = s.fine_print_conditions or []
        fp_lines = []
        for fp in fp_conditions:
            if isinstance(fp, dict) and fp.get("text"):
                cat = fp.get("category", "rule").upper()
                fp_lines.append(f"[{cat}] {fp.get('text')}")
        fine_print_summary = "; ".join(fp_lines) if fp_lines else "None specified"

        # Bilingual domain keywords for high-precision cross-lingual retrieval
        CAT_KEYWORDS = {
            "Agriculture & Farmers": "कृषि, किसान, खेती, फसल, MSP, न्यूनतम समर्थन मूल्य, agriculture, farmers, crops, cultivation",
            "Water & Sanitation": "जल, पानी, पेयजल, स्वच्छता, शौचालय, जल जीवन, water, sanitation, toilet, drinking water",
            "Electricity & Energy": "बिजली, विद्युत, ऊर्जा, सौर ऊर्जा, सोलर, रूफटॉप सोलर, electricity, solar, energy, power",
            "Food Security & Public Distribution": "खाद्य सुरक्षा, राशन, राशन कार्ड, खाद्यान्न, अन्न योजना, मुफ्त राशन, food security, ration card, foodgrains, PDS, ration",
            "Labour, Employment & Worker Welfare": "श्रम, श्रमिक, मजदूर, रोजगार, कामगार, दिहाड़ी, unorganized worker, labour, employment, worker, livelihood",
            "Education & Learning": "शिक्षा, छात्रवृत्ति, स्कॉलरशिप, स्कूल, कॉलेज, विद्यार्थी, education, scholarship, student",
            "Women & Child": "महिला, नारी, कन्या, बेटी, विधवा, बच्चे, पोषण, women, child, widow, girl child, mother",
            "Health & Wellness": "स्वास्थ्य, चिकित्सा, इलाज, अस्पताल, दवा, आरोग्य, health, medical, wellness, hospital",
            "Housing & Shelter": "आवास, मकान, घर, पक्का मकान, छत, housing, shelter, home, pucca house",
        }
        TYPE_KEYWORDS = {
            "price_support_mechanism": "MSP, Minimum Support Price, न्यूनतम समर्थन मूल्य, मूल्य समर्थन",
            "procurement_program": "सरकारी खरीद, अनाज खरीद, wheat procurement, paddy procurement, mandi",
            "public_distribution_program": "राशन वितरण, सार्वजनिक वितरण प्रणाली, राशन योजना, ration distribution, fair price shop, PDS",
            "social_security": "पेंशन, सामाजिक सुरक्षा, मासिक आर्थिक सहायता, pension, social security, monthly financial assistance",
            "credit_support": "ऋण, लोन, किसान क्रेडिट कार्ड, KCC, credit support, loan, subsidy",
            "insurance_program": "बीमा, सुरक्षा बीमा, फसल बीमा, insurance",
            "subsidized_inputs": "सब्सिडी, उर्वरक, बीज, कृषि यंत्र, subsidized inputs, seeds, fertilizer",
            "employment_program": "रोजगार योजना, मानदेय, स्वरोजगार, employment, self employment",
            "infrastructure_program": "अवसंरचना, निर्माण, infrastructure, construction",
            "welfare_scheme": "कल्याणकारी योजना, सरकारी सहायता, welfare assistance",
        }

        cat_tag = CAT_KEYWORDS.get(s.category, "")
        type_tag = TYPE_KEYWORDS.get(s.scheme_type, "")

        # Format required documents safely (handles strings, OR-group lists, and dicts)
        doc_list = []
        for d in (s.required_documents or []):
            if isinstance(d, list):
                doc_list.append(" OR ".join(str(item) for item in d))
            elif isinstance(d, dict):
                doc_list.append(str(d.get("accepts") or d.get("purpose") or d))
            else:
                doc_list.append(str(d))
        docs_summary = ", ".join(doc_list) if doc_list else "None specified"

        # Complete semantic representation covering all key criteria
        doc_text = (
            f"Scheme Name: {s.name}\n"
            f"Government: {s.government_name} ({s.government_level})\n"
            f"Scheme Type: {s.scheme_type} - {type_tag}\n"
            f"Category: {s.category} - {cat_tag}\n"
            f"Ministry / Department: {s.ministry or s.department or 'N/A'}\n"
            f"Description: {s.description or ''}\n"
            f"Eligibility: {eligibility_summary}\n"
            f"Fine-Print Rules & Exclusions: {fine_print_summary}\n"
            f"Benefits: {s.benefits or ''}\n"
            f"Required Documents: {docs_summary}\n"
            f"Application Process: {s.application_process or ''}"
        ).strip()

        documents.append(doc_text)
        metadatas.append({
            "scheme_id": s.id,
            "name": s.name,
            "slug": s.slug or "",
            "government_level": s.government_level or "Central",
            "government_name": s.government_name or "Central Government",
            "scheme_type": s.scheme_type or "welfare_scheme",
            "beneficiary_type": s.beneficiary_type or "individual",
            "status": s.status or "active",
            "category": s.category,
            "source_url": s.source_url,
            "has_fine_print": bool(fp_conditions),
        })
        ids.append(f"scheme_{s.id}")

    logger.info(f"Computing multilingual embeddings for {len(documents)} scheme documents...")
    embeddings = model.encode(documents, batch_size=32, show_progress_bar=True, normalize_embeddings=True)

    os.makedirs(CHROMA_DIR, exist_ok=True)
    logger.info(f"Initializing Chroma persistent client at: {CHROMA_DIR}")
    client = chromadb.PersistentClient(
        path=CHROMA_DIR,
        settings=chromadb.config.Settings(anonymized_telemetry=False)
    )

    # Re-create collection for clean, idempotent rebuild
    try:
        client.delete_collection(COLLECTION_NAME)
        logger.info(f"Cleared existing collection '{COLLECTION_NAME}'")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    logger.info("Adding documents and embeddings to Chroma...")
    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings.tolist(),
        metadatas=metadatas
    )

    total_indexed = collection.count()
    logger.info(f"Index build complete! Successfully indexed {total_indexed} schemes into Chroma DB.")


if __name__ == "__main__":
    build_index()
