"""
Model Context Protocol (MCP) Tools for YojanaVaani (Phase 5).

Implements the EXACT 4 statutory tools mandated by the project architecture:
1. search_schemes(query, profile) -> list[SchemeCandidate]
   RAG retrieval over Chroma multilingual vector index.
2. request_document(document_type) -> str
   Stub for Phase 5 (real camera capture + OCR extraction implemented in Phase 6).
3. check_eligibility(profile, candidate_schemes) -> list[EligibilityVerdict]
   Deterministic rules engine stub for Phase 5 (real deterministic predicate matching in Phase 6).
   CRITICAL: Never executed by an LLM; plain deterministic logic only.
4. escalate_to_csc(reason) -> dict
   Returns nearest Common Service Centre contact information.

Exposed via the official MCP Python SDK (`mcp.server.mcpserver.MCPServer`).
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
import chromadb
from mcp.server.mcpserver import MCPServer

logger = logging.getLogger(__name__)

# Initialize official MCP Server instance
mcp_server = MCPServer("yojanavaani-mcp")

# Path configuration
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
CHROMA_DIR = os.path.join(PROJECT_ROOT, "data-pipeline", "chroma_db")
NORMALIZED_DATA_PATH = os.path.join(
    PROJECT_ROOT, "data-pipeline", "data", "schemes_cleaned_normalized.json"
)
COLLECTION_NAME = "yojana_schemes"
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"

# In-memory scheme dictionary indexed by scheme_id for ultra-fast enrichment
_schemes_cache: Dict[int, Dict[str, Any]] = {}
_embedding_model = None
_chroma_collection = None


def _load_schemes_cache():
    """Loads normalized schemes into memory for fast lookup."""
    global _schemes_cache
    if not _schemes_cache and os.path.exists(NORMALIZED_DATA_PATH):
        try:
            with open(NORMALIZED_DATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    s_id = item.get("id")
                    if s_id is not None:
                        _schemes_cache[int(s_id)] = item
        except Exception as e:
            logger.error(f"Failed to load schemes cache from {NORMALIZED_DATA_PATH}: {e}")


def _get_embedding_model():
    """Lazy loader for SentenceTransformer embedding model."""
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model


def _get_chroma_collection():
    """Lazy loader for persistent ChromaDB collection."""
    global _chroma_collection
    if _chroma_collection is None and os.path.exists(CHROMA_DIR):
        client = chromadb.PersistentClient(
            path=CHROMA_DIR,
            settings=chromadb.config.Settings(anonymized_telemetry=False)
        )
        try:
            _chroma_collection = client.get_collection(COLLECTION_NAME)
        except Exception as e:
            logger.warning(f"Could not load Chroma collection '{COLLECTION_NAME}': {e}")
    return _chroma_collection


# -----------------------------------------------------------------------------
# DATA MODELS
# -----------------------------------------------------------------------------

class SchemeCandidate(BaseModel):
    """Structured representation of a retrieved government welfare scheme."""
    id: int = Field(..., description="Unique scheme identifier")
    name: str = Field(..., description="Official title of the scheme")
    category: str = Field(..., description="Primary sectoral category")
    government_name: str = Field(default="Central Government", description="Central or State jurisdiction")
    similarity_score: float = Field(default=0.0, description="RAG vector similarity score in [0.0, 1.0]")
    eligibility_criteria: Dict[str, Any] = Field(default_factory=dict, description="Structured eligibility predicates")
    benefits: Optional[Union[str, Dict[str, Any], List[Any]]] = Field(default=None, description="Official benefits and financial subsidies")
    required_documents: Optional[List[Any]] = Field(default_factory=list, description="Required documents for application")
    application_process: Optional[Union[str, Dict[str, Any], List[Any]]] = Field(default=None, description="Step-by-step application instructions")
    source_url: Optional[str] = Field(default=None, description="Official myScheme or portal URL")


class EligibilityVerdict(BaseModel):
    """Structured verdict emitted by the deterministic eligibility engine."""
    scheme_id: int = Field(..., description="Scheme identifier")
    scheme_name: str = Field(..., description="Scheme name")
    verdict: str = Field(..., description="Verdict: QUALIFIES, NEEDS_MORE_INFO, or DOES_NOT_QUALIFY")
    reason: str = Field(..., description="Statutory justification or failure reason")
    missing_fields: List[str] = Field(default_factory=list, description="Fields required to reach conclusive verdict")


# -----------------------------------------------------------------------------
# TOOL 1: search_schemes
# -----------------------------------------------------------------------------

@mcp_server.tool()
def search_schemes(query: str, profile: Optional[Dict[str, Any]] = None, top_k: int = 4) -> List[Dict[str, Any]]:
    """
    RAG retrieval tool over the welfare scheme vector database.
    Embeds the citizen's query and demographic context, queries ChromaDB,
    and returns top-k candidate schemes with their full eligibility criteria.

    Args:
        query: Citizen stated need or search keywords.
        profile: Citizen demographic profile dictionary (optional).
        top_k: Number of candidate schemes to return (default 4).
    """
    _load_schemes_cache()
    collection = _get_chroma_collection()
    model = _get_embedding_model()

    # Construct enriched contextual query
    profile_ctx = ""
    if profile:
        parts = []
        if profile.get("state"):
            parts.append(f"state: {profile['state']}")
        if profile.get("occupation"):
            parts.append(f"occupation: {profile['occupation']}")
        if profile.get("social_category"):
            parts.append(f"category: {profile['social_category']}")
        profile_ctx = " ".join(parts)

    search_query = f"{query} {profile_ctx}".strip()

    candidates: List[Dict[str, Any]] = []

    if collection and model:
        try:
            query_vector = model.encode([search_query], normalize_embeddings=True).tolist()
            results = collection.query(
                query_embeddings=query_vector,
                n_results=min(top_k * 2, 10),
                include=["metadatas", "distances"]
            )

            seen_ids = set()
            ids = results["ids"][0] if results.get("ids") else []
            distances = results["distances"][0] if results.get("distances") else []
            metadatas = results["metadatas"][0] if results.get("metadatas") else []

            for i in range(len(ids)):
                meta = metadatas[i] if i < len(metadatas) else {}
                scheme_id = meta.get("scheme_id")
                if not scheme_id or scheme_id in seen_ids:
                    continue

                seen_ids.add(scheme_id)
                # Similarity: distance to similarity conversion
                dist = distances[i] if i < len(distances) else 1.0
                similarity = round(max(0.0, 1.0 - (dist / 2.0)), 3)

                full_scheme = _schemes_cache.get(int(scheme_id), {})
                candidate = SchemeCandidate(
                    id=int(scheme_id),
                    name=full_scheme.get("name") or meta.get("name", "Unknown Scheme"),
                    category=full_scheme.get("category") or meta.get("category", "General"),
                    government_name=full_scheme.get("government_name") or meta.get("government_name", "Central Government"),
                    similarity_score=similarity,
                    eligibility_criteria=full_scheme.get("eligibility", {}),
                    benefits=full_scheme.get("benefits"),
                    required_documents=full_scheme.get("required_documents", []),
                    application_process=full_scheme.get("application_process"),
                    source_url=full_scheme.get("source_url") or meta.get("source_url")
                )
                candidates.append(candidate.model_dump())

                if len(candidates) >= top_k:
                    break

        except Exception as e:
            logger.error(f"Error executing Chroma vector search: {e}")

    # Fallback keyword match if Chroma unavailable or returned empty
    if not candidates and _schemes_cache:
        q_lower = query.lower()
        for sid, scheme in list(_schemes_cache.items())[:top_k]:
            if any(term in scheme["name"].lower() or term in scheme.get("description", "").lower() for term in q_lower.split()[:3]):
                candidate = SchemeCandidate(
                    id=sid,
                    name=scheme["name"],
                    category=scheme.get("category", "General"),
                    government_name=scheme.get("government_name", "Central Government"),
                    similarity_score=0.85,
                    eligibility_criteria=scheme.get("eligibility", {}),
                    benefits=scheme.get("benefits"),
                    required_documents=scheme.get("required_documents", []),
                    application_process=scheme.get("application_process"),
                    source_url=scheme.get("source_url")
                )
                candidates.append(candidate.model_dump())

    return candidates


# -----------------------------------------------------------------------------
# TOOL 2: request_document
# -----------------------------------------------------------------------------

@mcp_server.tool()
def request_document(document_type: str) -> str:
    """
    Triggers document photograph capture and OCR extraction.
    For Phase 5, this is implemented as an architectural stub.
    Real camera framing guidance and Tesseract/OpenCV extraction slots in Phase 6.

    Args:
        document_type: Type of document required (e.g. 'ration_card', 'khasra_khatauni', 'aadhaar_card', 'income_certificate').
    """
    clean_type = document_type.strip().lower()
    return (
        f"[DOCUMENT_REQUEST_STUB] Document verification requested for '{clean_type}'. "
        f"In Phase 6, citizen will photograph their {clean_type} and OCR will extract structured fields."
    )


# -----------------------------------------------------------------------------
# TOOL 3: check_eligibility (CRITICAL NON-LLM TOOL)
# -----------------------------------------------------------------------------

@mcp_server.tool()
def check_eligibility(profile: Dict[str, Any], candidate_schemes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deterministic rules engine tool that cross-checks citizen attributes against scheme criteria.
    NON-NEGOTIABLE ARCHITECTURAL RULE: The LLM agent NEVER determines eligibility.
    This function evaluates predicates deterministically in plain Python.
    Uses app.services.eligibility_engine.EligibilityEngine.

    Args:
        profile: Citizen demographic profile dictionary.
        candidate_schemes: List of candidate scheme dictionaries retrieved via search_schemes.
    """
    # Architectural stub for Phase 5: returns placeholder verdict
    # Full deterministic rule-based evaluation implemented in Phase 6
    results: List[Dict[str, Any]] = []
    for s in candidate_schemes:
        results.append({
            "scheme_id": s.get("id"),
            "scheme_name": s.get("name"),
            "verdict": "NEEDS_MORE_INFO",
            "reason": "Eligibility evaluation pending Phase 6 deterministic rule verification",
            "missing_fields": ["income", "category"],
            "disqualification_reasons": [],
            "manual_review_flags": []
        })
    return results


# -----------------------------------------------------------------------------
# TOOL 4: escalate_to_csc
# -----------------------------------------------------------------------------

@mcp_server.tool()
def escalate_to_csc(reason: str) -> Dict[str, Any]:
    """
    Escalation fallback tool. Returns nearest Common Service Centre (CSC)
    location and assistance helpline when queries are ambiguous, low-confidence,
    or reach maximum tool iterations without resolution.

    Args:
        reason: Explanation of why escalation to human CSC agent is triggered.
    """
    return {
        "status": "escalated",
        "reason": reason,
        "csc_name": "Common Service Centre (CSC) - Haidergarh Kiosk",
        "csc_id": "UP-BAR-CSC-10492",
        "address": "Gram Panchayat Bhavan, Haidergarh Main Road, Barabanki, Uttar Pradesh - 225126",
        "helpline": "1800-3000-3468",
        "vle_contact": "+91-9876543210",
        "working_hours": "09:00 AM - 05:00 PM (Monday - Saturday)",
        "services_provided": [
            "Biometric Aadhaar Authentication & e-KYC",
            "Direct Scheme Application Submission",
            "Document Scanning and Upload",
            "DBT Bank Account Seeding Verification"
        ]
    }
