# YojanaVaani — The Definitive Major Project Viva Master Guide & Defense Dossier

**Project Title:** YojanaVaani (योजनावाणी) — Voice-First AI Welfare Scheme Navigator for Indian Citizens  
**Academic Degree:** Bachelor of Technology (B.Tech) in Computer Science & Engineering (Major Project)  
**Author / Candidate:** Nikita Gupta & Project Team  
**Evaluation Date / Milestone:** Academic Year 2026 / Final Major Project Viva Examination  
**System Classification:** Voice-First Mobile Client (React Native Android) + Server-Side Agentic RAG (LangGraph + MCP) + Deterministic Eligibility Rules Engine  

---

# TABLE OF CONTENTS

1. [PART 0: VERIFIED PROJECT AUDIT & SYSTEM ARCHITECTURE](#part-0-verified-project-audit--system-architecture)
   - 0.1 Complete Verified Technology Stack
   - 0.2 System Architecture & Component Interactions
   - 0.3 Complete Repository Folder & File Directory
   - 0.4 Feature Implementation Status Matrix
   - 0.5 Dataset & Data Pipeline Details
   - 0.6 Model Inventory (Trained vs Fine-Tuned vs Pretrained vs API)
   - 0.7 Real Development Challenges & Verified Solutions
   - 0.8 Missing University / Project Details Checklist
   - 0.9 Executive Presentation Scripts (2-min, 5-min, and 10-min Walkthroughs)
2. [MODULE 1: Project Overview, Problem Formulation & Interaction Design](#module-1-project-overview-problem-formulation--interaction-design)
3. [MODULE 2: Mobile Frontend & Native Android Architecture](#module-2-mobile-frontend--native-android-architecture)
4. [MODULE 3: Backend Architecture & REST APIs (FastAPI & PostgreSQL)](#module-3-backend-architecture--rest-apis-fastapi--postgresql)
5. [MODULE 4: AI Agent Orchestration (LangGraph, MCP & Ollama)](#module-4-ai-agent-orchestration-langgraph-mcp--ollama)
6. [MODULE 5: Deterministic Eligibility Engine (Rule 2 Compliance)](#module-5-deterministic-eligibility-engine-rule-2-compliance)
7. [MODULE 6: Speech Processing Pipeline (Whisper ASR & Indic-TTS)](#module-6-speech-processing-pipeline-whisper-asr--indic-tts)
8. [MODULE 7: Computer Vision & Document OCR (OpenCV + Tesseract)](#module-7-computer-vision--document-ocr-opencv--tesseract)
9. [MODULE 8: Data Engineering, Embeddings & Vector Search (ChromaDB)](#module-8-data-engineering-embeddings--vector-search-chromadb)
10. [MODULE 9: Testing Strategy, Academic Benchmarks & Ethical Compliance](#module-9-testing-strategy-academic-benchmarks--ethical-compliance)
11. [MODULE 10: Complete Viva Question Bank (150+ Questions), Tough Traps & Master Defense](#module-10-complete-viva-question-bank-150-questions-tough-traps--master-defense)

---

# PART 0: VERIFIED PROJECT AUDIT & SYSTEM ARCHITECTURE

## 0.1 Complete Verified Technology Stack

| Layer / Subsystem | Claimed in Preliminary Specs | Actual Implemented Technology | Verified File in Codebase | Technical Verification & Viva Defense Notes |
|---|---|---|---|---|
| **Mobile Client** | React Native (CLI, TypeScript) | React Native `0.87.1`, React `19.2.3`, TypeScript `6.0.3` | `mobile/package.json` | Bare React Native CLI workflow (no Expo managed framework). Directly compiles to native Android APK. |
| **Mobile Navigation** | React Navigation / Native Stack | Top-level State Machine in `App.tsx` + React Navigation `7.x` | `mobile/App.tsx` | Screen transitions are handled via reactive state (`currentScreen`), preventing navigation stack lag during audio playback. |
| **Mobile Audio & Mic** | React Native Mic Recording | Native Kotlin Module: `AudioRecorderModule.kt` | `mobile/android/app/src/main/java/com/mobile/AudioRecorderModule.kt` | Custom Android `AudioRecord` module recording 16 kHz, 16-bit mono PCM/WAV directly to internal cache, converted to Base64. |
| **Offline Storage** | SQLite local database queue | In-Memory TypeScript Queue (`offlineQueue.ts`) | `mobile/src/services/offlineQueue.ts` | **Code Reality:** Implemented as an in-memory queue array (`queueStore`). Defend as an in-memory staging buffer that flushes on network reconnect. |
| **Backend Framework** | FastAPI (Python) | FastAPI `0.110.0+`, Uvicorn `0.28.0+`, Pydantic V2 | `backend/app/main.py` | Asynchronous REST server with CORS middleware, Pydantic settings, and sub-routers for speech, documents, and conversation. |
| **Relational Database** | PostgreSQL via SQLAlchemy | PostgreSQL 16 + SQLAlchemy `2.0+` + Alembic | `backend/app/models/scheme.py` | Relational scheme catalog with semi-structured JSONB columns for eligibility criteria and fine-print clauses. |
| **Vector Database** | ChromaDB or FAISS | **ChromaDB exclusively** | `backend/app/mcp/tools.py` | `chromadb.PersistentClient` pointing to `data-pipeline/chroma_db`, collection `yojana_schemes`. FAISS is completely absent. |
| **Embeddings** | Sentence-Transformers | `paraphrase-multilingual-mpnet-base-v2` | `backend/app/mcp/tools.py` | 768-dimensional dense vectors supporting cross-lingual semantic matching between colloquial Hindi queries and official metadata. |
| **Agent Orchestration** | LangGraph | LangGraph `0.1.0+` (`StateGraph`, Cyclical Graph) | `backend/app/services/agent.py` | Cyclical graph with nodes `agent_reasoning` and `execute_tools`. Bounded strictly to $\le 6$ tool iterations per turn. |
| **Tool Protocol** | Model Context Protocol (MCP) | Official Python SDK: `mcp.server.mcpserver.MCPServer` | `backend/app/mcp/tools.py` | Exposes exactly four statutory tools: `search_schemes`, `request_document`, `check_eligibility`, `escalate_to_csc`. |
| **Eligibility Engine** | Deterministic Python rules | `EligibilityEngine` (100% Deterministic Python) | `backend/app/services/eligibility_engine.py` | **Rule 2 Non-Negotiable:** Zero LLM in eligibility determination. Pure Python predicate evaluation. |
| **LLM Inference** | Open-weight via Ollama | Local Ollama: `llama3.2:3b` + Deterministic Fallback | `backend/app/services/agent.py` | Local open-weight LLM served via Ollama (`http://localhost:11434`), with an auditable rule-based fallback if Ollama is unreachable. |
| **Speech-to-Text (ASR)**| AI4Bharat IndicWhisper | `vasista22/whisper-hindi-small` (target `large-v2`) | `backend/app/services/asr_service.py` | Hugging Face Transformers pipeline with acoustic energy silence guard (`rms < 0.001`) and anti-repetition filters. |
| **Text-to-Speech (TTS)**| AI4Bharat Indic-TTS | Google Hindi Neural TTS + macOS Lekha Voice + Indic-TTS Hook | `backend/app/services/tts_service.py` | Hybrid architecture with LRU audio cache, phonetic normalizer (`normalize_phonetics_for_tts`), and 44.1 kHz ffmpeg normalization. |
| **Vision & OCR** | OpenCV + Tesseract OCR | OpenCV (`cv2`) + `pytesseract` (dual: `hin+eng`) | `backend/app/services/ocr_service.py` | Multi-stage image pipeline (deskew, CLAHE, adaptive thresholding) + specialized Indian document regex parsers. |
| **Deployment & Ops** | Docker / Docker Compose | `Dockerfile` + `docker-compose.yml` + `render.yaml` | Root repository files | Multi-container setup for local execution; Render cloud deployment blueprint. |

---

## 0.2 System Architecture & Component Interactions

```mermaid
flowchart TD
    User([Rural / Low-Literacy Citizen]) <-->|Spoken Hindi Audio & Camera Capture| MobileApp[React Native Native Android Client]
    
    subgraph MobileClient ["Mobile Client (Thin Client)"]
        MobileApp --> NativeMic[Kotlin AudioRecorderModule\n16kHz Mono PCM WAV]
        MobileApp --> Cam[react-native-image-picker\nDocument Capture]
        MobileApp --> NetQueue[offlineQueue.ts\nIn-Memory Retry Queue]
        MobileApp --> Speaker[Android MediaPlayer\nSpoken Response Playback]
    end

    MobileApp <-->|REST API / Multipart Base64 Audio| APIGateway[FastAPI Backend Server\nmain.py]

    subgraph ServerCompute ["Server-Side AI & Data Layer"]
        APIGateway <--> ASRService[Whisper Hindi ASR Service\nEnergy Guard + Hallucination Filter]
        APIGateway <--> TTSService[Vernacular TTS Service\nGoogle Neural + Lekha + FFMpeg]
        APIGateway <--> OCRService[OpenCV + Tesseract OCR\nDeskew + CLAHE + Dual-Pass]
        APIGateway <--> ConvManager[ConversationManager\nStage 1 Baseline Interview State Machine]
        
        ConvManager -->|Stage 1 Complete| AgentOrch[LangGraph Orchestration Agent\nCyclical State Graph, Bound <= 6]
        
        AgentOrch <-->|Official Python SDK| MCPTools[MCP Tool Suite\nmcp.server.mcpserver]
        
        MCPTools <-->|search_schemes| ChromaDB[(ChromaDB Vector Store\nyojana_schemes Collection\nparaphrase-multilingual-mpnet)]
        MCPTools <-->|check_eligibility| RuleEngine[Deterministic Eligibility Engine\n100% Python Predicates, Zero LLM]
        MCPTools <-->|request_document| OCRService
        MCPTools <-->|escalate_to_csc| CSCService[Common Service Centre Directory]
        
        APIGateway <--> PostgresDB[(PostgreSQL 16 Database\nschemes Table with JSONB Criteria)]
    end
```

### Architectural Principles:
1. **Thin-Client Separation:** Mobile application strictly handles UI, audio recording, camera capture, and playback. Zero AI inference runs on mobile to prevent battery drain, memory exhaustion, and thermal throttling.
2. **Deterministic Eligibility Guard (Rule 2):** LLMs are strictly forbidden from deciding whether a citizen qualifies for a scheme. The LangGraph agent only decides *when* to evaluate; the evaluation is executed by plain, rule-based Python logic.
3. **Bounded Cyclical Execution:** The agent is mathematically bounded to a maximum of 6 tool iterations per conversational turn, preventing infinite loops.
4. **Two-Stage Interaction Model:** Stage 1 executes a fixed 9-question baseline interview to guarantee profile completeness. Stage 2 executes the dynamic agentic search and verification loop.

---

## 0.3 Complete Repository Folder & File Directory

```
YojanaVaani/
├── AGENTS.md                          # Mandatory institutional & architectural constraints (PyTorch only, Rule 2)
├── CONTRIBUTING.md                    # 3-track ownership breakdown, git workflow, pre-PR checklist
├── Dockerfile                         # Production container image for FastAPI backend + OCR binaries
├── docker-compose.yml                 # Multi-container orchestration (PostgreSQL 16 + Backend)
├── render.yaml                        # Infrastructure-as-code cloud deployment blueprint
├── requirements-cloud.txt             # Consolidated production backend dependencies
├── Dataset.csv                        # Raw scraped dataset export (myScheme portal data dump)
│
├── backend/                           # FastAPI Backend Application Root
│   ├── app/
│   │   ├── main.py                    # Application entrypoint, CORS, sub-routers, offline HF flags
│   │   ├── core/
│   │   │   ├── config.py              # Pydantic Settings (DB URLs, Ollama endpoint, API keys)
│   │   │   └── database.py            # SQLAlchemy engine, session maker, declarative base
│   │   ├── api/
│   │   │   ├── conversation.py        # Core mobile conversation endpoints (/start, /respond, /document, /confirm)
│   │   │   ├── documents.py           # Standalone document upload and verification endpoints
│   │   │   ├── speech.py              # Standalone STT (/stt) and TTS (/tts) testing endpoints
│   │   │   └── health.py              # Liveness and readiness healthcheck (/health)
│   │   ├── models/
│   │   │   ├── conversation.py        # Pydantic models: CitizenProfile, ConversationState, Turn, Enums
│   │   │   └── scheme.py              # SQLAlchemy DB Model: Scheme table (JSONB criteria & fine-print)
│   │   ├── schemas/
│   │   │   └── scheme_preprocessed.py # Pydantic schemas for data validation and normalization
│   │   ├── services/
│   │   │   ├── baseline_interview.py  # 9 scripted Hindi questions, field mappings, validation regexes
│   │   │   ├── conversation_manager.py# Multi-turn session manager, vernacular answer parsers, history persistence
│   │   │   ├── agent.py               # LangGraph cyclical agent, Ollama Chat client, iteration limiter
│   │   │   ├── eligibility_engine.py  # 100% deterministic rule matching engine (Rule 2 statutory compliance)
│   │   │   ├── asr_service.py         # Whisper ASR provider, audio resampling, anti-hallucination energy guard
│   │   │   ├── tts_service.py         # Google Hindi neural TTS + macOS Lekha + Indic-TTS fallback, phonetic normalizer
│   │   │   └── ocr_service.py         # OpenCV image pipeline (CLAHE, deskew) + Tesseract dual-language OCR
│   │   └── mcp/
│   │       └── tools.py               # Official MCP Server exposing search_schemes, check_eligibility, request_doc, escalate
│   ├── alembic/                       # Database schema migration scripts (Versions 001 to 004)
│   ├── evaluation/                    # Phase 8 academic empirical benchmarking suite
│   │   ├── eval_asr.py                # Word Error Rate (WER) & Character Error Rate (CER) benchmark
│   │   ├── eval_retrieval.py          # Top-1, Top-3, Top-5 accuracy and Mean Reciprocal Rank (MRR)
│   │   ├── eval_hallucination.py      # Factual consistency and hallucination rate auditor
│   │   ├── eval_ocr.py                # Clean vs degraded document degradation gap evaluation
│   │   ├── eval_agent_trajectory.py   # Multi-turn tool call sequence sensibility auditor
│   │   ├── eval_e2e.py                # End-to-end task completion on 20 synthetic citizen profiles
│   │   └── evaluation_results.md      # Ground-truth numerical evaluation report for the thesis
│   └── tests/                         # Pytest test suite (43 automated tests, 100% passing)
│       ├── test_agent.py              # Agent tool routing, iteration bounds, state handoff tests
│       ├── test_conversation.py       # Baseline question sequence and vernacular parser tests
│       ├── test_conversation_api.py   # API contract tests for /conversation endpoints
│       ├── test_eligibility.py        # Rule engine test cases (age, income, caste, land bounds)
│       ├── test_ocr.py                # OpenCV preprocessing and field extraction tests
│       └── test_speech.py             # ASR transcription and TTS synthesis tests
│
├── mobile/                            # React Native Mobile Client Root (Bare Workflow)
│   ├── android/                       # Native Android Project
│   │   └── app/src/main/java/com/mobile/
│   │       ├── AudioRecorderModule.kt # Custom Kotlin NativeModule: 16kHz PCM WAV recording & MediaPlayer
│   │       └── AudioRecorderPackage.kt# React Native package registration
│   ├── src/
│   │   ├── config.ts                  # Backend endpoint URLs, ADB reverse proxy handling, healthcheck
│   │   ├── screens/
│   │   │   ├── OnboardingScreen.tsx   # Welcome screen, permission requests (Mic, Camera), voice intro
│   │   │   ├── ConversationScreen.tsx # Core voice interaction, pulsating mic visualizer, audio stream
│   │   │   ├── DocumentCaptureScreen.tsx# Camera viewfinder, capture review, OCR field confirmation
│   │   │   ├── ResultsScreen.tsx      # Ranked eligible schemes, qualification badges, audio playback
│   │   │   ├── SchemeDetailScreen.tsx # Detailed benefits, required documents, application process
│   │   │   ├── ProfileReportScreen.tsx# Structured citizen summary and verified document report
│   │   │   └── EscalationScreen.tsx   # Nearest Common Service Centre (CSC) address and helpline
│   │   └── services/
│   │       ├── audioService.ts        # TypeScript bridge to native AudioRecorderModule
│   │       ├── offlineQueue.ts        # In-memory retry queue for dropped mobile network packets
│   │       └── userHistoryService.ts  # Local assessment history persistence
│   └── __tests__/                     # Jest unit test suite for mobile UI screens
│
├── data-pipeline/                     # Scraping, Cleaning, Vector Indexing Root
│   ├── scrape_schemes.py              # Web scraper for myScheme.gov.in portal across 9 sectors
│   ├── clean_and_preprocess.py        # 11-step data audit and normalization pipeline
│   ├── build_index.py                 # ChromaDB vector embedding generator using MPNet
│   ├── extract_eligibility.py         # Regex and syntactic predicate extractor from raw text
│   ├── audit_extraction.py            # Quality auditor identifying unparsed clauses
│   ├── chroma_db/                     # Persistent ChromaDB vector database directory
│   └── data/
│       ├── schemes_cleaned_normalized.json # Final clean dataset (270 schemes)
│       └── flagged_for_review.json    # 13 low-confidence schemes flagged for manual review
│
└── docs/                              # Project Documentation & Reports
    ├── specification.md               # Master engineering specification & literature survey
    ├── architecture.md                # Architecture overview & component mapping
    ├── data_quality_report.md         # Detailed audit report on raw scraped data vs cleaned dataset
    └── major_project_report_ch1_to_ch4.md # Thesis report chapters (Introduction, Literature, Methodology)
```

---

## 0.4 Feature Implementation Status Matrix

| Feature | Design Specification | Codebase Implementation Status | Primary Implementation Files | Verification Evidence |
|---|---|---|---|---|
| **Voice Baseline Interview (Stage 1)** | 9 scripted Devanagari questions in fixed order. Captures demographic attributes. | **100% Completed** | `baseline_interview.py`, `conversation_manager.py` | [test_conversation.py](file:///Users/nikita/Documents/YojanaVaani/backend/tests/test_conversation.py) (7/7 passed). Vernacular parsers handle numbers ("पैंतीस", "35"), castes, and locations. |
| **Agentic Reasoning Loop (Stage 2)** | LangGraph cyclical agent deciding turn-by-turn tool calls. | **100% Completed** | `agent.py` | [test_agent.py](file:///Users/nikita/Documents/YojanaVaani/backend/tests/test_agent.py) (6/6 passed). StateGraph cycles between reasoning and tools. |
| **MCP Tool Protocol** | Exactly 4 statutory tools exposed via official MCP Python SDK. | **100% Completed** | `tools.py` | MCP server instantiated with `search_schemes`, `request_document`, `check_eligibility`, `escalate_to_csc`. |
| **Deterministic Eligibility Engine** | Zero LLM in verdict. Auditable rule evaluation across all demographic criteria. | **100% Completed** | `eligibility_engine.py` | [test_eligibility.py](file:///Users/nikita/Documents/YojanaVaani/backend/tests/test_eligibility.py) (11/11 passed). Emits `QUALIFIES`, `NEEDS_MORE_INFO`, `DOES_NOT_QUALIFY` with exact statutory clause reasons. |
| **Hindi Speech-to-Text (ASR)** | Server-side Whisper inference with anti-hallucination energy guard. | **100% Completed** | `asr_service.py` | [test_speech.py](file:///Users/nikita/Documents/YojanaVaani/backend/tests/test_speech.py) (7/7 passed). Energy guard drops silent audio; repetition filters block news loops. |
| **Hindi Text-to-Speech (TTS)** | Vernacular synthesis with natural Devanagari pronunciation. | **100% Completed** | `tts_service.py` | `normalize_phonetics_for_tts` prevents SC/ST from being mispronounced as "Supreme Court". Volume scaled to 75% via ffmpeg. |
| **Document Vision & OCR** | OpenCV preprocessing + Tesseract Hindi/English field extraction. | **100% Completed** | `ocr_service.py` | [test_ocr.py](file:///Users/nikita/Documents/YojanaVaani/backend/tests/test_ocr.py) (5/5 passed). Extracts Ration Card, Aadhaar, Income Certificate, and Khasra records. |
| **Semantic Vector Retrieval** | Multilingual embedding search over ChromaDB with query expansion. | **100% Completed** | `tools.py` | Vernacular expansion dictionary maps colloquial terms ("ठेला", "किसान", "सिलाई") into canonical terms. Evaluated at 57.1% Top-5 accuracy across 35 ground-truth pairs. |
| **Native Mobile App** | React Native Android app with live microphone and camera flows. | **100% Completed** | `mobile/App.tsx`, `mobile/src/screens/` | Built with native Kotlin `AudioRecorderModule`. 7 complete interactive screens. |
| **Offline Network Queue** | Buffers failed network responses until connectivity returns. | **Partially Implemented** (In-Memory Buffer) | `offlineQueue.ts` | Implemented in RAM array (`queueStore`). Retries queued items upon connectivity restoration. |
| **CSC Kiosk Escalation** | Fallback when tool iteration bound (6) is exceeded or query is ambiguous. | **100% Completed** | `tools.py`, `EscalationScreen.tsx` | Returns verified Haidergarh (Barabanki) CSC kiosk address, VLE phone contact, and toll-free helpline. |

---

## 0.5 Dataset & Data Pipeline Details

### A. Dataset Origin and Coverage
- **Source:** Web scraping of the official government portal [myScheme.gov.in](https://www.myscheme.gov.in/).
- **Total Schemes Collected & Verified:** **Exactly 270 schemes** (stored in `data-pipeline/data/schemes_cleaned_normalized.json`).
- **Governments Covered (3 Jurisdictions):**
  1. Central Government of India
  2. Government of NCT of Delhi
  3. Government of Uttar Pradesh
- **Sectors Covered (9 Priority Categories):**
  1. *Agriculture & Farmers* (e.g. PM-KISAN, PM-KUSUM Solar Pump, Crop Insurance)
  2. *Education & Learning* (e.g. Post-Matric Scholarships, Higher Education Assistance)
  3. *Women & Child* (e.g. Bal Seva Yojana, Destitute Widow Pension, Lakhpati Bitiya)
  4. *Health & Wellness* (e.g. Ayushman Bharat PM-JAY, Arogya Nidhi)
  5. *Housing & Shelter* (e.g. Pradhan Mantri Awas Yojana - Gramin & Urban)
  6. *Labour, Employment & Worker Welfare* (e.g. PM SVANidhi, PM Vishwakarma, BOCW Shramik Card)
  7. *Food Security & Public Distribution* (e.g. NFSA Antyodaya Anna Yojana, Ration Card)
  8. *Electricity & Energy* (e.g. Solar rooftop, rural electrification)
  9. *Water & Sanitation* (e.g. Swachh Bharat toilet subsidies, Jal Jeevan Mission)

### B. Structured Dataset Schema
Each scheme in `schemes_cleaned_normalized.json` and PostgreSQL `schemes` table contains:
- `id` (integer primary key)
- `name` (official title, e.g. "PM SVANidhi")
- `slug` (URL slug)
- `government_level` (Central / State)
- `government_name` (Central Government / Delhi Government / Uttar Pradesh Government)
- `category` (primary domain) & `categories` (JSON array of all related sectors)
- `description` (narrative explanation)
- `benefits` (structured monetary subsidy, monthly pension, or in-kind assets)
- `eligibility_criteria` (JSONB):
  - `min_age` (integer or null)
  - `max_age` (integer or null)
  - `income_ceiling` (float in INR or null)
  - `applicable_states` (list of strings, e.g. `["Uttar Pradesh"]`)
  - `social_category` (list of strings: `["General", "OBC", "SC", "ST"]`)
  - `gender` (`"Female"`, `"Male"`, `"Transgender"`, `"All"`)
  - `occupation` (e.g. `"Farmer"`, `"Street Vendor"`, `"Student"`)
  - `disability_status` (boolean or null)
  - `other_conditions_text` (unstructured statutory fine print)
- `required_documents` (JSON array of standard Indian identity/civic documents)
- `application_process` (Online / CSC / Offline steps)
- `source_url` (direct official portal verification link)
- `confidence_score` (extraction audit confidence score: $0.85 - 1.0$)

### C. 11-Step Data Cleaning Pipeline (`clean_and_preprocess.py`)
1. **Age Bound Repair (34 schemes):** Fixed regex negation errors (e.g. "not less than 18" parsed as max age) and swapped bounds (male 21 / female 18).
2. **False Semantic Anchor Removal:** Fixed instances where dependent child ages or years of state residency (e.g. "must reside in Delhi for 3 years") were erroneously captured as the applicant's age limit.
3. **Income Ceiling Extraction (62 schemes):** Converted textual income mentions (e.g. "वार्षिक आय 2 लाख रुपये से अधिक न हो") into numeric floats (`200000.0`).
4. **Social Category Overwrite Prevention (20 schemes):** Restored multi-caste eligibility arrays (`['SC', 'ST', 'OBC']`) where single regex tokens previously overwrote the field.
5. **Female Gender Default Leakage Repair (10 schemes):** Corrected generic welfare schemes mistakenly flagged as female-only due to words like "माता-पिता" (parents).
6. **Disability Prerequisite Flagging (17 schemes):** Verified that assistive device and disability pension schemes explicitly set `disability_status = True`.
7. **Document OR-Grouping:** Normalized flat document lists into statutory alternative groups (e.g. `[Aadhaar Card OR Voter ID]`).
8. **HTML & Markdown De-mangling:** Reconstructed tables crushed during scraping and stripped raw HTML `<br>` tags.
9. **Duplicate Scheme Family Linking (22 schemes):** Linked Central schemes with state-level counterparts (e.g. PMAY-Gramin with state supplements) via `scheme_family` and `parent_scheme_id`.
10. **Vector Embedding Ingestion:** Generated 768-dimensional normalized dense vectors for the `yojana_schemes` ChromaDB collection using `paraphrase-multilingual-mpnet-base-v2`.
11. **Low-Confidence Isolation:** 13 ambiguous schemes (4.8%) with complex administrative edge clauses were isolated into `flagged_for_review.json` for human oversight.

---

## 0.6 Model Inventory (Trained vs Fine-Tuned vs Pretrained vs API)

> [!IMPORTANT]
> **ACADEMIC HONESTY RULE:** Never claim you trained a model from scratch. Open-source foundation models and specialized fine-tunes were integrated, adapted, and constrained through software engineering and prompt architecture.

| Model / Subsystem | Organization / Provider | Exact Architecture | Task in YojanaVaani | Input / Output Format | Integration Type | Hardware & Runtime |
|---|---|---|---|---|---|---|
| **vasista22 Whisper Hindi** | Vasista22 (Hugging Face) | Transformer Encoder-Decoder (OpenAI Whisper) | Automatic Speech Recognition (ASR) for spoken Hindi | Input: 16 kHz Mono PCM Audio<br/>Output: Devanagari Hindi Text | **Pretrained Fine-tune**. Downloaded weights (`whisper-hindi-small` & `large-v2`). We did **NOT** train it. | PyTorch, cached in memory on backend server. Uses MPS (Apple Silicon), CUDA, or CPU. |
| **Sentence-Transformers MPNet** | UKPLab / Hugging Face | 12-layer Multilingual Transformer (`paraphrase-multilingual-mpnet-base-v2`) | Semantic embeddings for welfare scheme retrieval | Input: Spoken need + profile context<br/>Output: 768-dim dense vector | **Pretrained Foundation Model**. Downloaded weights. We did **NOT** train the embedding model. | PyTorch, offline local inference via SentenceTransformers library. |
| **Llama 3.2 3B** | Meta AI (served via Ollama) | Autoregressive Decoder Transformer | Orchestration agent reasoning in LangGraph | Input: Message state + MCP tool definitions<br/>Output: Tool calls (`search_schemes`, etc.) | **Pretrained Open-Weight LLM**. Served locally via Ollama runtime. We did **NOT** fine-tune or train it. | Local Ollama daemon (`http://localhost:11434`), 4-bit quantized. |
| **Tesseract OCR Engine** | Google / Ray Smith | LSTM Neural Network Character Recognizer (`tessdata_fast`) | Text extraction from citizen civic documents | Input: OpenCV preprocessed grayscale image<br/>Output: Hindi + English text strings | **Pretrained Open-Source OCR**. Language packs `hin.traineddata` + `eng.traineddata`. We did **NOT** train custom fonts. | C++ binary executed via `pytesseract` wrapper with custom regex parsing. |
| **Google Neural Hindi TTS** | Google (via `gTTS`) | Neural Concatenative / Parametric Synthesis | Spoken Hindi response generation for mobile playback | Input: Spoken Devanagari text<br/>Output: MP3 audio bytes (44.1 kHz) | **Turnkey TTS Engine / External API**. Integrated via `gTTS` library with local file caching. | Cloud HTTP endpoint with local LRU RAM cache + macOS Lekha offline fallback. |

---

## 0.7 Real Development Challenges & Verified Solutions

| Challenge | Root Cause | Real Error / Observed Symptom | Solution Implemented | Why This Solution Worked |
|---|---|---|---|---|
| **1. Whisper Hindi Hallucination on Silence** | Low-energy microphone capture caused Whisper's autoregressive decoder to hallucinate All India Radio broadcast transcripts or repeat loops. | Output generated: `"आकाशवाणी... प्रादेशिक समाचार... नमस्कार"` or repetitive loops when the user hesitated. | Implemented an acoustic energy guard (`rms_energy < 0.001`) and a regex/lexical diversity filter (`detect_hallucination_or_loop`) in `asr_service.py`. | Low-energy frames are dropped before invoking the neural decoder; repetitive n-grams are intercepted and discarded. |
| **2. Scraped Regex Negation & Age Swaps** | myScheme portal text had complex clauses like *"applicant must be not less than 18 and less than 60 years"*. Naive regex captured `18` as max age. | Scheme 475 set `min_age=None, max_age=18`, disqualifying adult applicants. | Built programmatic audit script `clean_and_preprocess.py` with exact syntactic regex rules and manual patch maps. | Cleaned 34 age anomalies and verified all 270 schemes against raw statutory prose. |
| **3. Mobile Audio Crackle & Clipping** | Synthesized speech sample rates (22.05 kHz or 24 kHz) mismatched the Android emulator's hardware audio mixer (`goldfish_audio`), causing buffer underruns. | Loud audio distortion, pops, and stutter during playback on Android devices. | Added `_resample_and_normalize_audio` using `ffmpeg` to resample all audio to standard 44.1 kHz and scale peak volume to 75% (-2.5 dBFS) in `tts_service.py`. | Eliminates digital clipping and gives the Android audio driver headroom to buffer cleanly. |
| **4. Hindi Phonetic Pronunciation Glitches** | Apple Lekha and TTS engines expanded abbreviation `"एससी"` (Scheduled Caste) to *"सुप्रीम कोर्ट"* (Supreme Court), and pronounced `"पुरुष"` with a dental 's'. | Spoken audio incorrectly said *"सुप्रीम कोर्ट वर्ग"* instead of Scheduled Caste, confusing rural citizens. | Created `normalize_phonetics_for_tts` in `tts_service.py` to expand abbreviations into full Devanagari (*"अनुसूचित जाति"*). | Guarantees clear vernacular articulation without relying on TTS engine guessing. |
| **5. OCR Perspective & Lighting Distortion** | Smartphone photos taken by rural citizens suffer from perspective tilt, shadows, and low resolution. | Raw Tesseract accuracy dropped to 66.7% on realistic mobile captures (a 33.3% degradation gap). | Created OpenCV preprocessing pipeline (CLAHE contrast normalization, contour deskew, adaptive thresholding) in `ocr_service.py` **plus** a UI touch confirmation step in `DocumentCaptureScreen.tsx`. | Maximizes OCR character clarity while allowing the citizen to inspect and correct extracted digits before statutory evaluation. |
| **6. Vernacular Search Vocabulary Mismatch** | Rural citizens describe needs in colloquial Hindi (*"ठेले के लिए लोन"*, *"सिलाई मशीन"*, *"बुढ़ापा पेंशन"*), whereas portal documents use formal English/Hindi titles (*"PM SVANidhi"*, *"Self-Employment Assistance"*). | Direct semantic vector search failed to retrieve PM SVANidhi when the user said *"ठेला"* (street cart). | Implemented the `VERNACULAR_EXPANSIONS` dictionary in `tools.py` to enrich search queries with administrative keywords. | Bridges the semantic vocabulary gap between colloquial spoken dialects and statutory portal metadata. |
| **7. Infinite Tool Calling Loop Risk** | If an LLM is unsure or candidate schemes repeatedly request additional data, an agent can loop indefinitely, exhausting tokens and freezing the app. | Unbounded cyclical agent could query the vector DB repeatedly without concluding. | Enforced a strict bound of `MAX_TOOL_ITERATIONS = 6` in LangGraph `agent.py`, forcing escalation to `escalate_to_csc` if limit is hit. | Guaranteed mathematical termination of the conversational turn within at most 6 tool steps. |

---

## 0.8 Missing University / Project Details Checklist

Before entering your viva hall, ensure you have these operational items committed to memory:
1. **Your Exact Track Ownership:** Defend your track from `CONTRIBUTING.md`:
   - *Track 1 (Backend & Agent):* LangGraph state graph, MCP tools, FastAPI endpoints, ASR/TTS singleton services.
   - *Track 2 (Mobile Client & Native):* React Native UI screens, Kotlin `AudioRecorderModule`, offline retry queue, audio playback.
   - *Track 3 (Data Pipeline & Vision):* myScheme scraping/cleaning, ChromaDB MPNet index, OpenCV-Tesseract OCR, Phase 8 evaluation suite.
2. **Institutional Rule Reminder:** If asked why TensorFlow/Keras was not used for embeddings or OCR, state clearly: *"Under university major project institutional guidelines, TensorFlow/Keras were strictly prohibited; our entire deep learning stack is built on PyTorch and classical computer vision."*

---

## 0.9 Executive Presentation Scripts

### 2-Minute Project Introduction (Elevator Pitch)
> *"Good morning, respected examiners. I am presenting **YojanaVaani**, a voice-first native Android application designed to bridge India's welfare awareness and accessibility divide for rural and low-literacy citizens. 
> 
> While official portals like myScheme aggregate over 2,000 welfare programs, they require high digital literacy, form-filling skills, and formal administrative vocabulary that rural citizens simply do not possess. YojanaVaani enables citizens to discover government schemes entirely by speaking in natural Hindi. 
> 
> Architecturally, it operates as a thin client where all AI inference runs server-side. The interaction follows a two-stage model: Stage 1 conducts a fixed, scripted 9-question baseline interview to gather demographic facts with zero LLM hallucination. Stage 2 triggers a LangGraph agent that calls four MCP tools to search a 270-scheme ChromaDB vector database, verify documents via OpenCV-Tesseract OCR, evaluate statutory eligibility through a 100% deterministic rules engine, or escalate to physical Common Service Centres. In our empirical benchmarks, the system achieved 100% factual faithfulness with zero eligibility hallucinations and a 57.1% Top-5 retrieval accuracy."*

### 5-Minute Technical Deep Dive
> *"To explain the engineering architecture in detail:
> 
> **1. Client-Side Layer:** We built a native Android application using bare React Native CLI and TypeScript. To achieve reliable audio recording without third-party library bloat, we wrote a custom Kotlin module—`AudioRecorderModule.kt`—which captures 16 kHz, 16-bit mono uncompressed PCM audio via Android's native `AudioRecord` API and streams Base64 WAV data to our backend.
> 
> **2. Conversational State Machine:** The backend is powered by FastAPI. When a session begins, `ConversationManager` executes Stage 1—a fixed 9-question baseline interview covering name, age, gender, state/district, income tier, caste reservation, occupation, disability, and stated need. Spoken responses are transcribed using a local fine-tune of Whisper Hindi (`vasista22/whisper-hindi-small`), filtered by our acoustic energy guard to prevent silence hallucinations.
> 
> **3. Agentic Orchestration Layer:** Once the baseline interview completes, control is handed over to our LangGraph state machine. The agent utilizes an open-weight LLM (`llama3.2:3b`) served locally via Ollama. It decides turn-by-turn which of exactly four tools to call over the Model Context Protocol (MCP): `search_schemes`, `request_document`, `check_eligibility`, and `escalate_to_csc`.
> 
> **4. The Non-Negotiable Rule 2:** A critical architectural rule of this project is that the LLM is strictly prohibited from determining eligibility. LLMs are probabilistic and prone to hallucinating age limits or benefit amounts. In YojanaVaani, the agent only identifies candidate schemes; qualification is evaluated by `check_eligibility`—a 100% deterministic Python rules engine that audits citizen facts against statutory criteria.
> 
> **5. Document Verification & Escalation:** If a scheme requires landholding proof or income certification, the agent triggers `request_document`. The citizen snaps a photo, which is preprocessed via OpenCV (deskewing, CLAHE contrast enhancement) and extracted via dual-language Tesseract OCR (`hin+eng`). If queries are ambiguous or reach our hard bound of 6 tool iterations, the system gracefully escalates to the nearest Common Service Centre kiosk."*

### 10-Minute Comprehensive Walkthrough Script
*(Use this script during your formal presentation slide deck walkthrough, detailing slide-by-slide motivation, data engineering, LangGraph cyclical flow, evaluation metrics, and live demo).*
