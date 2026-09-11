# AGENTS.md — YojanaVaani

This file is auto-prepended to every prompt processed in this repository. It contains only
the rules that constrain CODE — not the literature survey, report framing, or mentor-facing
content, which live in /docs/specification.md instead. If something here conflicts with a
specific phase prompt, the rule in this file wins unless the prompt explicitly says otherwise.

## What this project is

YojanaVaani is a voice-first native Android app (React Native) that helps Indian citizens --
especially rural and low-literacy users -- discover which government welfare schemes they
qualify for, entirely by speaking Hindi. This is a BTech CSE major project with academic
requirements attached; code quality and honest, auditable behavior matter as much as the
demo working.

## Non-negotiable architecture rules

1. **This is an agentic system with a bounded tool set, not a fixed pipeline.** An LLM-driven
   orchestration agent (built with LangGraph) decides, turn by turn, which of exactly four
   tools to call next. Do not hardcode a fixed call sequence in application logic -- the
   agent's reasoning decides the sequence.

2. **The eligibility verdict is NEVER decided by the LLM.** `check_eligibility` must always be
   plain, deterministic Python logic -- no LLM call inside it, ever. The agent may decide
   *when* to call this tool, but the tool itself must be auditable, rule-based code. If you
   are about to write a prompt or function that asks an LLM to directly state whether someone
   qualifies for a scheme, stop -- that logic belongs in `check_eligibility`, not agent
   reasoning.

3. **Tools are exposed via MCP (Model Context Protocol)**, using the official Python SDK
   (https://github.com/modelcontextprotocol/python-sdk). The four tools, with these exact
   names and responsibilities, are fixed -- do not add, remove, or rename them without being
   asked:
   - `search_schemes(query, profile)` -- RAG retrieval over the scheme vector index
   - `request_document(document_type)` -- triggers document capture + OCR extraction
   - `check_eligibility(profile, candidate_schemes)` -- deterministic rules engine (see rule 2)
   - `escalate_to_csc(reason)` -- returns nearest Common Service Centre info

4. **The agent is bounded**: maximum 6 tool-call iterations per conversational turn. If that
   limit is hit without resolution, escalate rather than loop further.

5. **Conversation has two fixed stages**:
   - Stage 1 -- a FIXED baseline interview in Hindi (name, age, gender, state/district, income
     bracket, social category, occupation, disability status, then an open "what help are you
     looking for" question), asked in the same order for every citizen. This is scripted, not
     agent-improvised.
   - Stage 2 -- the agentic follow-up loop (rule 1-4) begins only after Stage 1 completes.

6. **All AI inference runs server-side.** The React Native app is a lightweight client:
   audio/photo capture, playback, UI, and API calls only. Never put STT, TTS, RAG, OCR, or LLM
   inference logic inside the mobile app.

7. **This is a native mobile app, not a website or PWA.** Frontend is React Native compiled to
   a real installable APK. Do not build a browser-based or Progressive Web App interface.

## Fixed tech stack -- do not substitute without asking first

| Layer | Required technology |
|---|---|
| Backend | FastAPI (Python), SQLAlchemy, PostgreSQL |
| Mobile | React Native (TypeScript), React Native CLI (not Expo managed workflow) |
| Speech-to-text | AI4Bharat IndicWhisper (gated) with `vasista22` Whisper-large-v2 fine-tunes as the working default until/unless gated access is granted |
| Text-to-speech | AI4Bharat Indic-TTS or IndicF5 |
| OCR | Tesseract via pytesseract, Hindi + English language packs, with OpenCV pre-processing (deskew, contrast) |
| Embeddings | A multilingual sentence-transformers model (e.g. paraphrase-multilingual-mpnet-base-v2) |
| Vector database | FAISS or Chroma |
| RAG framework | LangChain |
| Agent orchestration | LangGraph |
| Tool protocol | Model Context Protocol (MCP), official python-sdk |
| LLM | Open-weight (Llama or Mistral family) served locally via Ollama -- not a commercial API |
| Local mobile storage | SQLite (for offline queuing) |
| Containerization | Docker / docker-compose |

**Explicitly forbidden anywhere in this codebase**: TensorFlow, Keras, MATLAB. This is an
institutional rule from the course, not a preference -- if a library you'd reach for depends
on TensorFlow/Keras under the hood, use a PyTorch-based or classical-ML alternative instead.

## Data and privacy rules

- The scheme corpus is scraped from https://www.myscheme.gov.in/. For v1, scope this to 4-5
  categories most relevant to target users (e.g. Agriculture, Education, Women & Child,
  Health, Housing) -- do not attempt to scrape and index all 2,300+ schemes; that is out of
  scope for a semester project.
- Never use real people's actual identity documents (ration cards, Aadhaar, income
  certificates) anywhere in the codebase, tests, or sample data -- including your own. Use
  self-created, clearly synthetic mock documents only.
- Treat all citizen data (voice recordings, document images, extracted fields) as sensitive:
  encrypt in transit and at rest, minimize what's retained, and never send it to a third-party
  API without explicit disclosure. This reflects India's Digital Personal Data Protection Act,
  2023 -- data minimization and purpose limitation are real constraints on this system's
  design, not just report material.

## Repository structure

```
/backend          -- FastAPI app (app/api, app/models, app/services, app/mcp, app/core)
/mobile            -- React Native app (TypeScript)
/data-pipeline     -- scraping, structuring, and vector-index-building scripts
/backend/evaluation -- evaluation/metrics scripts (Phase 8 onward)
/docs              -- specification.md (full project spec) and architecture notes
docker-compose.yml
```

## Definition of done for any task

- Do not report a phase or task complete without actually running the verification yourself
  (a test script, a curl call, an emulator run) -- state clearly what you ran and what it
  returned, not just "this should work."
- If a metric or test result is weak, report it honestly rather than omitting it or only
  showing best-case numbers -- this is an academic project where honest evaluation is part of
  the deliverable, not a product where only good news matters.
- When a phase's task depends on a previous phase's output (e.g. the RAG tool depends on the
  vector index from the data pipeline), check that the dependency actually exists and works
  before building on top of it -- don't assume.

## Full project context

The complete project specification -- literature survey, detailed component explanations,
full requirements list, evaluation plan, and academic framing -- lives in
`/docs/specification.md`. Refer to it for background on *why* a decision was made; this file
is the authoritative source for *what rules the code must follow*.
