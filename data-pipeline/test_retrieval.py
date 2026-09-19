"""
Semantic retrieval test script for YojanaVaani Phase 2.
CLI tool to query the multilingual Chroma vector index and verify retrieval quality.

Tests cross-lingual matching for English, Hindi, and Hinglish queries.
Usage:
    python test_retrieval.py "MSP wheat procurement support for farmer in Uttar Pradesh"
    python test_retrieval.py "Delhi widow pension"
    python test_retrieval.py "solar electricity subsidy"
    python test_retrieval.py "गरीब परिवार के लिए राशन योजना"
    python test_retrieval.py "UP किसान सहायता योजना"
"""

import os
import sys
import logging
import chromadb
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.WARNING)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CHROMA_DIR = os.path.join(PROJECT_ROOT, "data-pipeline", "chroma_db")
COLLECTION_NAME = "yojana_schemes"
MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"


def search(query: str, top_k: int = 5):
    if not os.path.exists(CHROMA_DIR):
        print(f"Error: Chroma index not found at {CHROMA_DIR}. Run build_index.py first!")
        return

    client = chromadb.PersistentClient(
        path=CHROMA_DIR,
        settings=chromadb.config.Settings(anonymized_telemetry=False)
    )
    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception as e:
        print(f"Error: Collection '{COLLECTION_NAME}' not found in Chroma: {e}")
        return

    model = SentenceTransformer(MODEL_NAME)
    query_vector = model.encode([query], normalize_embeddings=True).tolist()

    results = collection.query(
        query_embeddings=query_vector,
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    print(f"\n=======================================================")
    print(f" Query: \"{query}\"")
    print(f" Top-{top_k} Multilingual Semantic Matches:")
    print(f"=======================================================\n")

    items = results["ids"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]
    documents = results["documents"][0]

    for rank, (item_id, dist, meta, doc) in enumerate(zip(items, distances, metadatas, documents), 1):
        similarity = 1.0 - dist
        name = meta.get("name", "Unknown")
        gov = meta.get("government_name", "Central Government")
        scheme_type = meta.get("scheme_type", "welfare_scheme")
        category = meta.get("category", "General")
        url = meta.get("source_url", "")

        # Extract brief description or benefits from document text
        lines = [l.strip() for l in doc.split("\n") if l.strip()]
        desc_line = next((l for l in lines if l.startswith("Description:")), "")
        benefits_line = next((l for l in lines if l.startswith("Benefits:")), "")

        preview = (desc_line or benefits_line or lines[0])[0:180]

        print(f"{rank}. {name}")
        print(f"   Jurisdiction: {gov}")
        print(f"   Scheme Type:  {scheme_type}")
        print(f"   Category:     {category}")
        print(f"   Similarity:   {similarity:.4f} (distance: {dist:.4f})")
        print(f"   URL:          {url}")
        print(f"   Preview:      {preview}...")
        print("-------------------------------------------------------")
    print()


def main():
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        search(query)
    else:
        print("YojanaVaani Multilingual Semantic Retrieval CLI")
        print("Type a query (or 'quit' to exit):")
        while True:
            try:
                query = input("\nQuery > ").strip()
                if query.lower() in ["quit", "exit", "q"]:
                    break
                if not query:
                    continue
                search(query)
            except (KeyboardInterrupt, EOFError):
                break


if __name__ == "__main__":
    main()
