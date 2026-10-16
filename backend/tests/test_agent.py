"""
Unit tests for LangGraph Agentic Layer and MCP Tools — Phase 5.
"""

import pytest
import json
from app.mcp.tools import (
    search_schemes,
    request_document,
    check_eligibility,
    escalate_to_csc,
    SchemeCandidate,
    EligibilityVerdict,
)
from app.services.agent import YojanaVaaniAgent, AgentRunResult, MAX_TOOL_ITERATIONS
from app.services.conversation_manager import ConversationManager
from app.models.conversation import ConversationStatus


def test_mcp_search_schemes():
    """Verify search_schemes returns candidate schemes with full criteria."""
    results = search_schemes(query="किसान सोलर पंप सिंचाई सहायता", top_k=3)
    assert len(results) > 0
    first = results[0]
    assert "name" in first
    assert "id" in first
    assert "eligibility_criteria" in first
    assert "category" in first


def test_mcp_request_document_stub():
    """Verify request_document returns structured placeholder message."""
    msg = request_document("ration_card")
    assert "ration_card" in msg
    assert "DOCUMENT_REQUEST_STUB" in msg


def test_mcp_check_eligibility_stub():
    """Verify check_eligibility executes deterministic checks and returns structured verdicts."""
    profile = {
        "age": 42,
        "state": "Uttar Pradesh",
        "gender": "Female",
        "approx_income_bracket": "below_2_lakh",
        "disability_status": False
    }
    candidate_schemes = [
        {
            "id": 101,
            "name": "PM Solar Pump Scheme",
            "eligibility_criteria": {"min_age": 18, "max_age": 60, "state_restriction": "Uttar Pradesh"},
            "required_documents": ["Khasra Khatauni"]
        },
        {
            "id": 102,
            "name": "Youth Entrepreneurship Scheme",
            "eligibility_criteria": {"min_age": 18, "max_age": 35},
            "required_documents": []
        }
    ]

    verdicts = check_eligibility(profile, candidate_schemes)
    assert len(verdicts) == 2

    # First scheme needs land records
    v1 = next(v for v in verdicts if v["scheme_id"] == 101)
    assert v1["verdict"] in ["QUALIFIES", "NEEDS_MORE_INFO"]

    # Second scheme fails on age (42 > 35)
    v2 = next(v for v in verdicts if v["scheme_id"] == 102)
    assert v2["verdict"] == "DOES_NOT_QUALIFY"
    assert "exceeds maximum permissible age" in v2["reason"]


def test_mcp_escalate_to_csc():
    """Verify escalate_to_csc returns Common Service Centre contact details."""
    res = escalate_to_csc("Ambiguous query")
    assert res["status"] == "escalated"
    assert "csc_name" in res
    assert "helpline" in res
    assert "address" in res


def test_agent_run_iteration_bound():
    """Verify that agent enforces maximum 6 iterations bound."""
    agent = YojanaVaaniAgent()
    profile = {
        "name": "रामवती",
        "age": 42,
        "gender": "Female",
        "state": "Uttar Pradesh",
        "occupation": "Farmer"
    }
    res: AgentRunResult = agent.run(profile, "सोलर पंप सहायता")
    assert res.iteration_count <= MAX_TOOL_ITERATIONS
    assert "search_schemes" in res.tools_called
    assert len(res.candidate_schemes) > 0


def test_conversation_manager_agentic_handoff():
    """Verify ConversationManager transitions to Agentic Follow-Up loop after baseline interview."""
    manager = ConversationManager()
    session = manager.create_conversation("conv_agentic_test")
    cid = session.conversation_id

    # Simulate answering all 9 questions
    answers = [
        ("name", "रामवती"),
        ("age", "42"),
        ("gender", "महिला"),
        ("state_district", "उत्तर प्रदेश, बाराबंकी"),
        ("approx_income_bracket", "2 लाख से कम"),
        ("social_category", "ओबीसी"),
        ("occupation", "खेती"),
        ("disability_status", "नहीं"),
        ("stated_need", "सोलर पंप योजना"),
    ]
    for field, ans in answers:
        manager.record_answer(cid, field, ans)

    assert session.status == ConversationStatus.scheme_matching
    assert session.baseline_complete is True

    # Run agentic follow-up
    updated_session = manager.run_agentic_followup(cid)
    assert updated_session.status in [
        ConversationStatus.results_ready,
        ConversationStatus.awaiting_document,
        ConversationStatus.escalated,
    ]
    assert len(updated_session.candidate_schemes) > 0
