"""
Model Context Protocol (MCP) package for YojanaVaani.
Exposes statutory tools via official MCP Python SDK.
"""

from app.mcp.tools import (
    SchemeCandidate,
    EligibilityVerdict,
    search_schemes,
    request_document,
    check_eligibility,
    escalate_to_csc,
    mcp_server,
)

__all__ = [
    "SchemeCandidate",
    "EligibilityVerdict",
    "search_schemes",
    "request_document",
    "check_eligibility",
    "escalate_to_csc",
    "mcp_server",
]
