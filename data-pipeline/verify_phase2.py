"""
Verification and Spot-Check Script for Phase 2.
Executes the 5 required semantic retrieval test queries and performs
a comprehensive audit / 10-scheme spot-check on the PostgreSQL database.
"""

import os
import json
import chromadb
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CHROMA_DIR = os.path.join(PROJECT_ROOT, "data-pipeline", "chroma_db")
COLLECTION_NAME = "yojana_schemes"
MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://yojana:yojana123@localhost:5432/yojanavaani"
)


def run_retrieval_tests():
    print("=" * 80)
    print("PART 1: MULTILINGUAL SEMANTIC RETRIEVAL TEST SUITE (5 QUERIES)")
    print("=" * 80)

    test_queries = [
        "MSP wheat procurement support for farmer in Uttar Pradesh",
        "Delhi widow pension",
        "solar electricity subsidy",
        "गरीब परिवार के लिए राशन योजना",
        "UP किसान सहायता योजना"
    ]

    client = chromadb.PersistentClient(
        path=CHROMA_DIR,
        settings=chromadb.config.Settings(anonymized_telemetry=False)
    )
    collection = client.get_collection(COLLECTION_NAME)
    model = SentenceTransformer(MODEL_NAME)

    for i, q in enumerate(test_queries, 1):
        print(f"\n[{i}/5] TEST QUERY: \"{q}\"")
        print("-" * 60)
        q_vec = model.encode([q], normalize_embeddings=True).tolist()
        res = collection.query(
            query_embeddings=q_vec,
            n_results=3,
            include=["documents", "metadatas", "distances"]
        )

        for rank, (doc_id, dist, meta, doc) in enumerate(
            zip(res["ids"][0], res["distances"][0], res["metadatas"][0], res["documents"][0]), 1
        ):
            sim = 1.0 - dist
            name = meta.get("name", "Unknown")
            gov = meta.get("government_name", "Unknown")
            stype = meta.get("scheme_type", "Unknown")
            cat = meta.get("category", "Unknown")
            url = meta.get("source_url", "")
            
            lines = [l.strip() for l in doc.split("\n") if l.strip()]
            desc = next((l for l in lines if l.startswith("Description:")), lines[0] if lines else "")
            print(f"  Rank {rank}: {name}")
            print(f"    Gov: {gov} | Type: {stype} | Cat: {cat} | Sim: {sim:.4f}")
            print(f"    URL: {url}")
            print(f"    Snippet: {desc[:140]}...")


def run_database_audit_and_spot_check():
    print("\n" + "=" * 80)
    print("PART 2: POSTGRESQL DATABASE SPOT-CHECK (10 DIVERSE SCHEMES)")
    print("=" * 80)

    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM schemes")).scalar()
        print(f"\nTotal schemes in PostgreSQL: {total}")

        gov_counts = conn.execute(
            text("SELECT government_name, COUNT(*) FROM schemes GROUP BY government_name ORDER BY count DESC")
        ).fetchall()
        print("Breakdown by Government:")
        for g, c in gov_counts:
            print(f"  - {g}: {c}")

        # Pick 10 representative schemes across Central, Delhi, and UP
        sample_queries = [
            # 1. Central MSP / Agriculture
            "SELECT * FROM schemes WHERE category = 'Agriculture & Farmers' AND government_name = 'Central Government' AND (scheme_type = 'price_support_mechanism' OR name ILIKE '%market%' OR name ILIKE '%kisan%') LIMIT 1",
            # 2. Central Solar / Energy
            "SELECT * FROM schemes WHERE category = 'Electricity & Energy' AND government_name = 'Central Government' LIMIT 1",
            # 3. Central Food Security / Ration
            "SELECT * FROM schemes WHERE category = 'Food Security & Public Distribution' AND government_name = 'Central Government' LIMIT 1",
            # 4. Central Labour Welfare
            "SELECT * FROM schemes WHERE category = 'Labour, Employment & Worker Welfare' AND government_name = 'Central Government' LIMIT 1",
            # 5. Central Water & Sanitation
            "SELECT * FROM schemes WHERE category = 'Water & Sanitation' AND government_name = 'Central Government' LIMIT 1",
            # 6. Delhi Widow / Women Pension
            "SELECT * FROM schemes WHERE government_name = 'Delhi Government' AND (name ILIKE '%widow%' OR name ILIKE '%distress%' OR name ILIKE '%women%') LIMIT 1",
            # 7. Delhi Health / Welfare
            "SELECT * FROM schemes WHERE government_name = 'Delhi Government' AND category = 'Health & Wellness' LIMIT 1",
            # 8. Delhi Education / Students
            "SELECT * FROM schemes WHERE government_name = 'Delhi Government' AND category = 'Education & Learning' LIMIT 1",
            # 9. UP Agriculture / Farmer
            "SELECT * FROM schemes WHERE government_name = 'Uttar Pradesh Government' AND category = 'Agriculture & Farmers' LIMIT 1",
            # 10. UP Pension / Divyangjan / Social Security
            "SELECT * FROM schemes WHERE government_name = 'Uttar Pradesh Government' AND (category = 'Labour, Employment & Worker Welfare' OR name ILIKE '%pension%' OR name ILIKE '%divyang%') LIMIT 1"
        ]

        sample_ids = []
        for sq in sample_queries:
            row = conn.execute(text(sq)).mappings().first()
            if row and row["id"] not in sample_ids:
                sample_ids.append(row["id"])

        # If less than 10, fill with other schemes
        if len(sample_ids) < 10:
            extra_rows = conn.execute(text(f"SELECT id FROM schemes WHERE id NOT IN ({','.join(str(i) for i in sample_ids)}) LIMIT {10 - len(sample_ids)}")).fetchall()
            sample_ids.extend([r[0] for r in extra_rows])

        print(f"\nInspecting {len(sample_ids)} schemes in detail:\n")

        for idx, sid in enumerate(sample_ids, 1):
            row = conn.execute(text("SELECT * FROM schemes WHERE id = :sid"), {"sid": sid}).mappings().first()
            elig = row["eligibility_criteria"] or {}
            fine_print = row["fine_print_conditions"] or []
            docs = row["required_documents"] or []

            print(f"[{idx}] {row['name']}")
            print(f"    ID: {row['id']} | Slug: {row['slug']}")
            print(f"    Jurisdiction: {row['government_level']} | {row['government_name']}")
            print(f"    Category: {row['category']} | Scheme Type: {row['scheme_type']}")
            print(f"    Ministry/Dept: {row['ministry']} / {row['department']}")
            print(f"    URL: {row['source_url']}")
            print(f"    Description: {str(row['description'])[:120]}... (len: {len(str(row['description']))})")
            print(f"    Benefits: {str(row['benefits'])[:120]}... (len: {len(str(row['benefits']))})")
            print(f"    Structured Eligibility:")
            print(f"      min_age: {elig.get('min_age')}, max_age: {elig.get('max_age')}, income_ceiling: {elig.get('income_ceiling')}")
            print(f"      gender: {elig.get('gender')}, social_category: {elig.get('social_category')}, occupation: {elig.get('occupation')}")
            print(f"      disability_status: {elig.get('disability_status')}, state_restriction: {elig.get('state_restriction')}")
            other_cond = elig.get('other_conditions_text', '')
            print(f"      other_conditions_text: {other_cond[:140]}... (len: {len(other_cond)})")
            print(f"    Fine-Print Conditions ({len(fine_print)} total):")
            if fine_print:
                for f_idx, fp in enumerate(fine_print[:2], 1):
                    cat = fp.get('category', 'rule')
                    txt = fp.get('text', '')
                    verif = fp.get('verifiable_from_profile', False)
                    print(f"      [{f_idx}] [{cat.upper()}] (Profile-verifiable: {verif}) -> {txt[:110]}...")
            else:
                print(f"      None extracted (no restrictive fine-print patterns detected)")
            print(f"    Required Documents ({len(docs)} total):")
            if docs:
                docs_sample = [', '.join(d) if isinstance(d, list) else str(d) for d in docs[:3]]
                print(f"      Sample: {'; '.join(docs_sample)}...")
            print("-" * 80)


if __name__ == "__main__":
    run_retrieval_tests()
    run_database_audit_and_spot_check()
