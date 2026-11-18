"""
LangGraph Agentic Reasoning Layer for YojanaVaani (Phase 5).

Architectural Rules:
1. Dynamic Tool-Calling Agent: Uses LangGraph to orchestrate a cyclic state machine.
   The agent decides turn-by-turn which of the 4 MCP tools to call.
2. The eligibility verdict is NEVER decided by the LLM:
   All eligibility decisions are strictly routed to the deterministic `check_eligibility` tool.
   The LLM only decides WHEN to search, WHEN to ask clarifying questions, WHEN to request documents,
   and WHEN to evaluate.
3. Bounded Iterations: Hard maximum of 6 tool-call iterations per turn to guarantee termination.
   If limit is reached without resolution, forces escalation via `escalate_to_csc`.
4. Stage 2 Handoff: Triggered once ConversationManager completes Stage 1 baseline interview
   (`status == 'scheme_matching'`).
"""

import os
import json
import logging
from typing import Annotated, Any, Dict, List, Optional, TypedDict
from pydantic import BaseModel, Field

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from app.mcp.tools import (
    search_schemes as mcp_search_schemes,
    request_document as mcp_request_document,
    check_eligibility as mcp_check_eligibility,
    escalate_to_csc as mcp_escalate_to_csc,
)

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 6
DEFAULT_OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")

HINDI_SCHEME_NAME_MAP = {
    "divyang": "दिव्यांगजन पेंशन योजना",
    "old age": "वृद्धावस्था पेंशन योजना",
    "widow": "निराश्रित विधवा पेंशन योजना",
    "surgical grant": "दिव्यांगता रोकथाम शल्य चिकित्सा अनुदान",
    "pm-kisan": "प्रधानमंत्री किसान सम्मान निधि",
    "pm kisan": "प्रधानमंत्री किसान सम्मान निधि",
    "pm svanidhi": "पीएम स्वनिधि योजना",
    "awaas": "प्रधानमंत्री आवास योजना",
    "ayushman": "आयुष्मान भारत योजना",
    "scholarship": "छात्रवृत्ति योजना",
    "tricycle": "मोटराइज्ड ट्राइसाइकिल सहायता योजना",
    "motorized": "मोटराइज्ड ट्राइसाइकिल सहायता योजना",
    "artificial limb": "कृत्रिम अंग सहायता योजना",
    "family benefit": "राष्ट्रीय पारिवारिक लाभ योजना",
}

def to_hindi_scheme_name(name: str) -> str:
    if not name:
        return "सरकारी कल्याणकारी योजना"
    n_lower = name.lower()
    for k, v in HINDI_SCHEME_NAME_MAP.items():
        if k in n_lower:
            return v
    if any("\u0900" <= c <= "\u097F" for c in name):
        return name
    clean = name.replace("Yojana", "योजना").replace("Scheme", "योजना").replace("Pension", "पेंशन").replace("Grant", "अनुदान")
    return clean


# -----------------------------------------------------------------------------
# LANGCHAIN WRAPPERS FOR MCP TOOLS
# -----------------------------------------------------------------------------

@tool
def search_schemes(query: str) -> str:
    """
    RAG retrieval tool over the government scheme vector database.
    Searches for relevant welfare schemes matching the citizen's need.
    """
    results = mcp_search_schemes(query=query)
    return json.dumps(results, ensure_ascii=False)


@tool
def request_document(document_type: str) -> str:
    """
    Triggers document photograph capture and OCR extraction.
    Use when a candidate scheme requires specific proof (ration card, land records, income proof).
    """
    return mcp_request_document(document_type=document_type)


@tool
def check_eligibility(reason: str = "statutory criteria check") -> str:
    """
    DETERMINISTIC RULES ENGINE TOOL.
    Evaluates whether the citizen qualifies for retrieved candidate schemes based on their profile.
    CRITICAL: Never state an eligibility verdict yourself — always call this tool.
    """
    return "Evaluated candidate schemes eligibility"


@tool
def escalate_to_csc(reason: str) -> str:
    """
    Escalates the query to the nearest Common Service Centre (CSC) when assistance is needed,
    information is contradictory, or no matching schemes can be found.
    """
    csc = mcp_escalate_to_csc(reason=reason)
    return json.dumps(csc, ensure_ascii=False)


TOOLS_LIST = [search_schemes, request_document, check_eligibility, escalate_to_csc]
TOOLS_BY_NAME = {t.name: t for t in TOOLS_LIST}


# -----------------------------------------------------------------------------
# LANGGRAPH STATE DEFINITION
# -----------------------------------------------------------------------------

class AgentGraphState(TypedDict):
    """Runtime state dictionary passed through LangGraph nodes."""
    citizen_profile: Dict[str, Any]
    stated_need: str
    messages: Annotated[List[BaseMessage], add_messages]
    iteration_count: int
    candidate_schemes: List[Dict[str, Any]]
    missing_facts: List[str]
    verdicts: List[Dict[str, Any]]
    final_response_type: str  # "results_ready", "ask_followup", "request_document", "escalated"
    final_response_text: str
    csc_info: Optional[Dict[str, Any]]
    tools_called: List[str]
    collected_documents: List[Dict[str, Any]]


class AgentRunResult(BaseModel):
    """Structured result returned by the agent after execution."""
    tools_called: List[str] = Field(default_factory=list, description="Ordered sequence of tools executed")
    candidate_schemes: List[Dict[str, Any]] = Field(default_factory=list, description="Candidate schemes retrieved")
    missing_facts: List[str] = Field(default_factory=list, description="Identified missing criteria facts")
    verdicts: List[Dict[str, Any]] = Field(default_factory=list, description="Eligibility verdicts emitted by rules tool")
    response_type: str = Field(..., description="Action type: results_ready, ask_followup, request_document, or escalated")
    response_text: str = Field(..., description="Spoken vernacular Hindi response to citizen")
    csc_info: Optional[Dict[str, Any]] = Field(default=None, description="Common Service Centre details if escalated")
    iteration_count: int = Field(default=0, description="Total tool call iterations executed")


# -----------------------------------------------------------------------------
# SYSTEM PROMPT
# -----------------------------------------------------------------------------

AGENT_SYSTEM_PROMPT = """You are YojanaVaani's government welfare scheme navigator assistant for Indian citizens.
You are helping a citizen discover schemes they qualify for based on their demographic profile and stated need.

AVAILABLE TOOLS:
1. `search_schemes(query)`: RAG vector search over official scheme database.
2. `request_document(document_type)`: Triggers camera document capture (e.g. ration card, khasra land record).
3. `check_eligibility(candidate_schemes_json)`: Deterministic rules engine. Evaluates statutory criteria.
4. `escalate_to_csc(reason)`: Escalates to nearest Common Service Centre kiosk.

MANDATORY BEHAVIORAL CONSTRAINTS:
1. You MUST call `search_schemes` first using the citizen's stated need and profile facts.
2. Reason ONLY from information retrieved via search_schemes. NEVER invent scheme rules, subsidies, or names.
3. CRITICAL DESIGN RULE: YOU MUST NEVER STATE AN ELIGIBILITY VERDICT DIRECTLY IN YOUR GENERATED TEXT.
   Eligibility is NEVER an LLM decision. You must ALWAYS call `check_eligibility` to evaluate criteria.
4. If candidate schemes require a specific document or asset verification not present in the citizen's profile,
   either call `request_document(document_type)` or ask a single short clarifying question in plain Hindi text (not a tool call).
5. Once you have candidate schemes, call `check_eligibility` with the candidate schemes list.
6. If the citizen's query is out of scope, irrelevant, or after multiple tool calls no schemes match, call `escalate_to_csc`.
7. You have a hard bound of 6 tool-call iterations per turn.
"""


class YojanaVaaniAgent:
    """
    Orchestration agent utilizing LangGraph and an open-weight LLM served via Ollama.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or DEFAULT_OLLAMA_MODEL
        self._llm = None
        self._graph = None
        self._init_llm()
        self._build_graph()

    def _init_llm(self):
        """Initializes Ollama chat model client."""
        try:
            from langchain_ollama import ChatOllama
            self._llm = ChatOllama(
                model=self.model_name,
                temperature=0.0,
                num_predict=256,
                client_kwargs={"timeout": 30.0},
                base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
            ).bind_tools(TOOLS_LIST)
            logger.info(f"Initialized ChatOllama with model='{self.model_name}'")
        except Exception as e:
            logger.warning(f"Could not connect to ChatOllama: {e}. Will use agentic fallback.")
            self._llm = None

    def _build_graph(self):
        """Constructs the LangGraph cyclical tool-calling workflow."""
        builder = StateGraph(AgentGraphState)

        builder.add_node("agent_reasoning", self._agent_node)
        builder.add_node("execute_tools", self._tools_node)

        builder.set_entry_point("agent_reasoning")

        # Conditional branch from agent reasoning
        builder.add_conditional_edges(
            "agent_reasoning",
            self._route_decision,
            {
                "execute_tools": "execute_tools",
                "end": END
            }
        )

        # After tools execution, loop back to agent reasoning
        builder.add_edge("execute_tools", "agent_reasoning")

        self._graph = builder.compile()

    def _agent_node(self, state: AgentGraphState) -> Dict[str, Any]:
        """Agent reasoning node that invokes the LLM or applies fallback decision logic."""
        iter_count = state.get("iteration_count", 0)

        # Hard iteration bound check: if 6 reached, force escalate to CSC
        if iter_count >= MAX_TOOL_ITERATIONS:
            logger.warning(f"Maximum iteration limit ({MAX_TOOL_ITERATIONS}) reached. Forcing escalation.")
            csc = mcp_escalate_to_csc(reason="Maximum of 6 tool-call iterations reached without resolution.")
            return {
                "iteration_count": iter_count,
                "final_response_type": "escalated",
                "csc_info": csc,
                "final_response_text": (
                    "आपकी आवश्यकता के लिए नियमों की जटिलता अधिक है। हमने आपके निकटतम कॉमन सर्विस सेंटर (CSC) "
                    "का विवरण भेज दिया है जहाँ निःशुल्क मानवीय सहायता उपलब्ध है।"
                ),
                "messages": [AIMessage(content="Escalated to CSC due to iteration limit bound.")]
            }

        # If check_eligibility or escalate_to_csc was already executed, conclude with deterministic summary:
        tools_called = state.get("tools_called", [])
        if "check_eligibility" in tools_called or "escalate_to_csc" in tools_called:
            verdicts = state.get("verdicts", [])
            qual_names = [v["scheme_name"] for v in verdicts if v.get("verdict") == "QUALIFIES"]
            if qual_names:
                h_name = to_hindi_scheme_name(qual_names[0])
                if len(qual_names) == 1:
                    hindi_resp = f"बधाई हो! आप {h_name} के लिए पात्र हैं। नीचे योजना की पूरी जानकारी दी गई है।"
                else:
                    hindi_resp = f"बधाई हो! आप {len(qual_names)} सरकारी योजनाओं के लिए पात्र हैं, जिसमें {h_name} शामिल है।"
                final_type = "results_ready"
            elif verdicts:
                h_first = to_hindi_scheme_name(verdicts[0].get("scheme_name", ""))
                hindi_resp = f"जाँच पूरी हो गई है। {h_first}: {verdicts[0].get('reason', 'नियमों के अनुसार पात्रता सत्यापित नहीं हुई।')}"
                final_type = "results_ready"
            else:
                hindi_resp = "आपकी आवश्यकता के लिए नियमों की जटिलता अधिक है। हमने आपके निकटतम कॉमन सर्विस सेंटर (CSC) का विवरण तैयार किया है जहाँ निःशुल्क मानवीय सहायता उपलब्ध है।"
                final_type = "escalated"

            return {
                "final_response_type": final_type,
                "final_response_text": hindi_resp,
                "messages": [AIMessage(content=hindi_resp)]
            }

        # If LLM is available, invoke it with conversation messages
        if self._llm is not None:
            try:
                messages = state["messages"]
                response = self._llm.invoke(messages)
                tool_calls = getattr(response, "tool_calls", None)
                if tool_calls and len(tool_calls) > 0:
                    return {"messages": [response]}

                # If LLM did not emit tool calls, enforce mandatory architectural rules:
                candidates = state.get("candidate_schemes", [])
                tools_called = state.get("tools_called", [])

                # Step 1: search_schemes MUST always be executed first
                if "search_schemes" not in tools_called:
                    tool_call = {
                        "name": "search_schemes",
                        "args": {"query": state.get("stated_need", "")},
                        "id": f"call_search_{iter_count+1}",
                        "type": "tool_call"
                    }
                    return {"messages": [AIMessage(content="", tool_calls=[tool_call])]}

                # Step 2: If candidate schemes exist, route through check_eligibility or request_document
                if candidates and "check_eligibility" not in tools_called and "request_document" not in tools_called and "escalate_to_csc" not in tools_called:
                    first_scheme = candidates[0]
                    req_docs = str(first_scheme.get("required_documents", "")).lower()
                    criteria = str(first_scheme.get("eligibility_criteria", {})).lower()

                    collected_docs = state.get("collected_documents") or []
                    collected_types = set()
                    for doc in collected_docs:
                        if isinstance(doc, dict) and doc.get("document_type"):
                            collected_types.add(str(doc["document_type"]).lower())

                    # Check for needed documents that citizen has NOT yet uploaded
                    needed_doc = None
                    if ("khasra" in req_docs or "land" in req_docs or "khasra" in criteria) and ("khasra_khatauni" not in collected_types and "land_record" not in collected_types):
                        needed_doc = "khasra_khatauni"
                    elif ("income" in req_docs or "वार्षिक आय" in req_docs or "आय प्रमाण" in req_docs) and "income_certificate" not in collected_types:
                        needed_doc = "income_certificate"
                    elif ("ration" in req_docs or "राशन" in req_docs or "bpl" in req_docs) and "ration_card" not in collected_types:
                        needed_doc = "ration_card"
                    elif ("aadhaar" in req_docs or "आधार" in req_docs or "identity" in req_docs) and "aadhaar_card" not in collected_types:
                        needed_doc = "aadhaar_card"

                    if needed_doc and "request_document" not in tools_called:
                        tool_call = {
                            "name": "request_document",
                            "args": {"document_type": needed_doc},
                            "id": f"call_doc_{iter_count+1}",
                            "type": "tool_call"
                        }
                        return {"messages": [AIMessage(content="", tool_calls=[tool_call])]}

                    tool_call = {
                        "name": "check_eligibility",
                        "args": {"reason": "statutory criteria check"},
                        "id": f"call_eligibility_{iter_count+1}",
                        "type": "tool_call"
                    }
                    return {"messages": [AIMessage(content="", tool_calls=[tool_call])]}

                # Step 3: If search_schemes was called and no candidate schemes found, escalate to CSC
                if not candidates and "escalate_to_csc" not in tools_called:
                    tool_call = {
                        "name": "escalate_to_csc",
                        "args": {"reason": f"No statutory schemes found matching query '{state.get('stated_need')}'"},
                        "id": f"call_escalate_{iter_count+1}",
                        "type": "tool_call"
                    }
                    return {"messages": [AIMessage(content="", tool_calls=[tool_call])]}

                # Post-tool execution: synthesize final Hindi response from deterministic tool verdicts
                verdicts = state.get("verdicts", [])
                qual_names = [v["scheme_name"] for v in verdicts if v.get("verdict") == "QUALIFIES"]
                if qual_names:
                    h_name = to_hindi_scheme_name(qual_names[0])
                    if len(qual_names) == 1:
                        hindi_resp = f"बधाई हो! आप {h_name} के लिए पात्र हैं। नीचे योजना की पूरी जानकारी दी गई है।"
                    else:
                        hindi_resp = f"बधाई हो! आप {len(qual_names)} सरकारी योजनाओं के लिए पात्र हैं, जिसमें {h_name} शामिल है।"
                    final_type = "results_ready"
                elif verdicts:
                    h_first = to_hindi_scheme_name(verdicts[0].get("scheme_name", ""))
                    hindi_resp = f"जाँच पूरी हो गई है। {h_first}: {verdicts[0].get('reason', 'नियमों के अनुसार पात्रता सत्यापित नहीं हुई।')}"
                    final_type = "results_ready"
                elif state.get("csc_info"):
                    hindi_resp = "आपकी आवश्यकता के लिए नियमों की जटिलता अधिक है। हमने आपके निकटतम कॉमन सर्विस सेंटर (CSC) का विवरण तैयार किया है जहाँ निःशुल्क मानवीय सहायता उपलब्ध है।"
                    final_type = "escalated"
                else:
                    hindi_resp = getattr(response, "content", "") or "आपकी जानकारी के आधार पर योजना नियमों की जाँच पूरी कर ली गई है।"
                    final_type = "ask_followup"

                return {
                    "final_response_type": final_type,
                    "final_response_text": hindi_resp,
                    "messages": [AIMessage(content=hindi_resp)]
                }
            except Exception as e:
                logger.error(f"Error in LLM invocation: {e}. Falling back to deterministic agent reasoning.")

        # Deterministic agent reasoning path (used when Ollama is offline or for guaranteed unit test consistency)
        return self._deterministic_agent_step(state)

    def _deterministic_agent_step(self, state: AgentGraphState) -> Dict[str, Any]:
        """
        Deterministic, auditable decision step mirroring the LLM agent prompt.
        Ensures 100% reproducible behavior across all test scenarios.
        """
        tools_called = state.get("tools_called", [])
        candidates = state.get("candidate_schemes", [])
        stated_need = state.get("stated_need", "")
        profile = state.get("citizen_profile", {})

        # 1. Step 1: Must call search_schemes first
        if "search_schemes" not in tools_called:
            tool_call = {
                "name": "search_schemes",
                "args": {"query": stated_need},
                "id": "call_search_1",
                "type": "tool_call"
            }
            return {"messages": [AIMessage(content="", tool_calls=[tool_call])]}

        # 2. Step 2: Analyze retrieved schemes for missing facts or documents
        if candidates and "check_eligibility" not in tools_called:
            first_scheme = candidates[0]
            req_docs = str(first_scheme.get("required_documents", "")).lower()
            criteria = first_scheme.get("eligibility_criteria", {})

            collected_docs = state.get("collected_documents") or []
            collected_types = set()
            for doc in collected_docs:
                if isinstance(doc, dict) and doc.get("document_type"):
                    collected_types.add(str(doc["document_type"]).lower())

            needed_doc = None
            if ("khasra" in req_docs or "land" in req_docs or "khasra" in str(criteria).lower()) and ("khasra_khatauni" not in collected_types and "land_record" not in collected_types):
                needed_doc = "khasra_khatauni"
            elif ("income" in req_docs or "वार्षिक आय" in req_docs or "आय प्रमाण" in req_docs) and "income_certificate" not in collected_types:
                needed_doc = "income_certificate"
            elif ("ration" in req_docs or "राशन" in req_docs or "bpl" in req_docs) and "ration_card" not in collected_types:
                needed_doc = "ration_card"
            elif ("aadhaar" in req_docs or "आधार" in req_docs or "identity" in req_docs) and "aadhaar_card" not in collected_types:
                needed_doc = "aadhaar_card"

            if needed_doc and "request_document" not in tools_called:
                tool_call = {
                    "name": "request_document",
                    "args": {"document_type": needed_doc},
                    "id": "call_doc_1",
                    "type": "tool_call"
                }
                return {"messages": [AIMessage(content="", tool_calls=[tool_call])]}

            # Otherwise, evaluate eligibility via deterministic rules tool
            tool_call = {
                "name": "check_eligibility",
                "args": {"reason": "statutory criteria check"},
                "id": "call_eligibility_1",
                "type": "tool_call"
            }
            return {"messages": [AIMessage(content="", tool_calls=[tool_call])]}

        # 3. If no candidate schemes found or query is out-of-scope, escalate
        if not candidates and "escalate_to_csc" not in tools_called:
            tool_call = {
                "name": "escalate_to_csc",
                "args": {"reason": f"No statutory schemes found matching query '{stated_need}'"},
                "id": "call_escalate_1",
                "type": "tool_call"
            }
            return {"messages": [AIMessage(content="", tool_calls=[tool_call])]}

        # 4. Final summary synthesis after check_eligibility
        verdicts = state.get("verdicts", [])
        qual_names = [v["scheme_name"] for v in verdicts if v.get("verdict") == "QUALIFIES"]
        if qual_names:
            h_name = to_hindi_scheme_name(qual_names[0])
            if len(qual_names) == 1:
                hindi_resp = f"बधाई हो! आप {h_name} के लिए पात्र हैं। नीचे योजना की पूरी जानकारी दी गई है।"
            else:
                hindi_resp = f"बधाई हो! आप {len(qual_names)} सरकारी योजनाओं के लिए पात्र हैं, जिसमें {h_name} शामिल है।"
        else:
            hindi_resp = "आपकी जानकारी के आधार पर योजना नियमों की जाँच पूरी कर ली गई है।"

        return {
            "final_response_type": "results_ready",
            "final_response_text": hindi_resp,
            "messages": [AIMessage(content=hindi_resp)]
        }

    def _tools_node(self, state: AgentGraphState) -> Dict[str, Any]:
        """Executes tool calls generated by the agent."""
        last_message = state["messages"][-1]
        tool_calls = getattr(last_message, "tool_calls", [])

        tool_messages = []
        tools_called = list(state.get("tools_called", []))
        candidate_schemes = list(state.get("candidate_schemes", []))
        missing_facts = list(state.get("missing_facts", []))
        verdicts = list(state.get("verdicts", []))
        csc_info = state.get("csc_info")
        final_type = state.get("final_response_type", "")
        iter_count = state.get("iteration_count", 0)

        for tc in tool_calls:
            t_name = tc.get("name")
            t_args = tc.get("args", {})
            t_id = tc.get("id", "tool_call")

            tools_called.append(t_name)
            iter_count += 1

            if t_name == "search_schemes":
                query_str = t_args.get("query", state.get("stated_need", ""))
                prof = dict(state.get("citizen_profile", {}))
                if "stated_need" not in prof and state.get("stated_need"):
                    prof["stated_need"] = state.get("stated_need")
                top_k_arg = t_args.get("top_k", 5)
                res_schemes = mcp_search_schemes(query=query_str, profile=prof, top_k=top_k_arg)
                candidate_schemes = res_schemes
                output_str = json.dumps(res_schemes, ensure_ascii=False)

            elif t_name == "request_document":
                doc_type = t_args.get("document_type", "identity_document")
                doc_res = mcp_request_document(document_type=doc_type)
                missing_facts.append(f"document_{doc_type}")
                final_type = "request_document"
                output_str = doc_res

            elif t_name == "check_eligibility":
                # Execute deterministic rules tool
                prof = dict(state.get("citizen_profile", {}))
                if "stated_need" not in prof and state.get("stated_need"):
                    prof["stated_need"] = state.get("stated_need")
                res_verdicts = mcp_check_eligibility(profile=prof, candidate_schemes=candidate_schemes)
                verdicts = res_verdicts
                final_type = "results_ready"
                output_str = json.dumps(res_verdicts, ensure_ascii=False)

                # Enrich candidate_schemes with verdicts and sort by eligibility rank
                verdict_map = {v.get("scheme_id"): v for v in res_verdicts if v.get("scheme_id")}
                verdict_name_map = {v.get("scheme_name", "").strip().lower(): v for v in res_verdicts if v.get("scheme_name")}

                enriched_candidates = []
                for cs in candidate_schemes:
                    cs_copy = dict(cs)
                    v_match = verdict_map.get(cs_copy.get("id")) or verdict_name_map.get(cs_copy.get("name", "").strip().lower())
                    if v_match:
                        cs_copy["verdict"] = v_match.get("verdict")
                        cs_copy["reason"] = v_match.get("reason")
                        cs_copy["disqualification_reasons"] = v_match.get("disqualification_reasons", [])
                        cs_copy["missing_fields"] = v_match.get("missing_fields", [])
                    else:
                        cs_copy["verdict"] = "NEEDS_MORE_INFO"
                        cs_copy["reason"] = "पात्रता नियमों की पुष्टि आवश्यक है।"
                    enriched_candidates.append(cs_copy)

                # Deterministic sorting: QUALIFIES (0) -> NEEDS_MORE_INFO (1) -> DOES_NOT_QUALIFY (2)
                v_rank = {"QUALIFIES": 0, "NEEDS_MORE_INFO": 1, "DOES_NOT_QUALIFY": 2}
                enriched_candidates.sort(key=lambda s: v_rank.get(s.get("verdict", ""), 3))
                candidate_schemes = enriched_candidates

            elif t_name == "escalate_to_csc":
                reason = t_args.get("reason", "Query unresolved")
                csc_data = mcp_escalate_to_csc(reason=reason)
                csc_info = csc_data
                final_type = "escalated"
                output_str = json.dumps(csc_data, ensure_ascii=False)

            else:
                output_str = f"Error: Unknown tool '{t_name}'"

            tool_messages.append(ToolMessage(content=output_str, tool_call_id=t_id))

        return {
            "messages": tool_messages,
            "tools_called": tools_called,
            "iteration_count": iter_count,
            "candidate_schemes": candidate_schemes,
            "missing_facts": missing_facts,
            "verdicts": verdicts,
            "csc_info": csc_info,
            "final_response_type": final_type
        }

    def _route_decision(self, state: AgentGraphState) -> str:
        """Determines whether to execute tools or terminate the graph."""
        if state.get("final_response_type") in ["escalated", "results_ready"] and not getattr(state["messages"][-1], "tool_calls", None):
            return "end"

        last_message = state["messages"][-1]
        tool_calls = getattr(last_message, "tool_calls", None)

        if tool_calls and len(tool_calls) > 0:
            return "execute_tools"

        return "end"

    def run(
        self,
        citizen_profile: Dict[str, Any],
        stated_need: str,
        collected_documents: Optional[List[Dict[str, Any]]] = None
    ) -> AgentRunResult:
        """
        Executes the agentic loop on a citizen profile and stated need.
        Returns the structured AgentRunResult with full trajectory details.
        """
        init_messages = [
            SystemMessage(content=AGENT_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Citizen Profile: {json.dumps(citizen_profile, ensure_ascii=False)}\n"
                    f"Stated Need: \"{stated_need}\"\n"
                    f"Please find matching government schemes and evaluate statutory eligibility."
                )
            )
        ]

        init_state: AgentGraphState = {
            "citizen_profile": citizen_profile,
            "stated_need": stated_need,
            "messages": init_messages,
            "iteration_count": 0,
            "candidate_schemes": [],
            "missing_facts": [],
            "verdicts": [],
            "final_response_type": "",
            "final_response_text": "",
            "csc_info": None,
            "tools_called": [],
            "collected_documents": collected_documents or []
        }

        final_state = self._graph.invoke(init_state)

        # Determine final response type and text
        resp_type = final_state.get("final_response_type")
        if not resp_type:
            if final_state.get("verdicts"):
                resp_type = "results_ready"
            elif final_state.get("csc_info"):
                resp_type = "escalated"
            else:
                resp_type = "ask_followup"

        resp_text = final_state.get("final_response_text", "")
        if not resp_text:
            last_msg = final_state["messages"][-1]
            resp_text = getattr(last_msg, "content", "") or "योजना की जानकारी प्राप्त कर ली गई है।"

        candidate_schemes = final_state.get("candidate_schemes", [])
        verdicts = final_state.get("verdicts", [])
        if verdicts and candidate_schemes:
            verdict_map = {v.get("scheme_id"): v for v in verdicts if v.get("scheme_id")}
            verdict_name_map = {v.get("scheme_name", "").strip().lower(): v for v in verdicts if v.get("scheme_name")}
            for cs in candidate_schemes:
                if not cs.get("verdict"):
                    v_match = verdict_map.get(cs.get("id")) or verdict_name_map.get(cs.get("name", "").strip().lower())
                    if v_match:
                        cs["verdict"] = v_match.get("verdict")
                        cs["reason"] = v_match.get("reason")
                        cs["disqualification_reasons"] = v_match.get("disqualification_reasons", [])
                        cs["missing_fields"] = v_match.get("missing_fields", [])
            v_rank = {"QUALIFIES": 0, "NEEDS_MORE_INFO": 1, "DOES_NOT_QUALIFY": 2}
            candidate_schemes.sort(key=lambda s: v_rank.get(s.get("verdict", ""), 3))

        return AgentRunResult(
            tools_called=final_state.get("tools_called", []),
            candidate_schemes=candidate_schemes,
            missing_facts=final_state.get("missing_facts", []),
            verdicts=verdicts,
            response_type=resp_type,
            response_text=resp_text,
            csc_info=final_state.get("csc_info"),
            iteration_count=final_state.get("iteration_count", 0)
        )
