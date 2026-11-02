# YojanaVaani (योजनावाणी) 🎙️🏛️

> **Voice-First Government Scheme Discovery for Rural and Low-Literacy Indian Citizens**  
> *B.Tech Major Project in Computer Science and Engineering*

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React Native](https://img.shields.io/badge/Mobile-React%20Native%20(CLI)-61DAFB.svg?logo=react&logoColor=black)](https://reactnative.dev)
[![PyTorch](https://img.shields.io/badge/AI%2FML-PyTorch-EE4C2C.svg?logo=pytorch&logoColor=white)](https://pytorch.org)
[![LangGraph](https://img.shields.io/badge/Agent-LangGraph-blue.svg)](https://github.com/langchain-ai/langgraph)
[![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-purple.svg)](https://www.trychroma.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📌 Abstract & Motivation

Over **800+ Central and State welfare schemes** exist in India to support rural households, smallholder farmers, women, and marginalized communities. However, millions of eligible citizens fail to access these benefits due to:
1. **The Literacy & Text Barrier**: Traditional government portals ([myScheme](https://www.myscheme.gov.in/)) require complex text navigation, typing search queries, and reading dense legal English/Hindi eligibility guidelines.
2. **The "Fine Print" Asymmetry**: Citizens often travel miles to district offices only to be rejected over obscure conditions (e.g., land ceiling, family income slabs, vehicle ownership criteria).
3. **The Hallucination Danger in LLMs**: Generic AI chatbots frequently invent non-existent government benefits or misstate income cutoffs, leading to citizen distress.

**YojanaVaani** is an agentic, voice-first system built specifically for rural Indian citizens. Citizens converse naturally in spoken **Hindi (Devanagari)**. The system carries out a structured baseline interview, retrieves official schemes using multilingual vector embeddings, uses an open-weight LLM agent to orchestrate follow-up queries and document OCR, and evaluates eligibility through a **deterministic, auditable rules engine (zero LLM hallucination in verdicts)**. If no match is found or an impasse is reached, it routes citizens to their nearest **Common Service Centre (CSC)**.

---

## 🏗️ System Architecture

All speech recognition, text-to-speech, optical character recognition, and agent orchestration run **server-side**. The Android app serves as a lightweight, resilient audio/photo capture client with local SQLite offline queuing.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   React Native Android Client (mobile)                 │
│   • Conversational Hindi Voice UI  • Animated Mic & Visualizer        │
│   • Camera Document Capture       • SQLite Offline Response Queue     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / Multipart Form-Data
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend Server                          │
│                                                                        │
│  ┌───────────────────────┐               ┌──────────────────────────┐  │
│  │   ASR Service (STT)   │               │    TTS Service (TTS)     │  │
│  │  Vasista Whisper L-v2 │               │    Indic-TTS Devanagari  │  │
│  └───────────┬───────────┘               └──────────▲───────────────┘  │
│              │ Transcribed Hindi Text               │ Spoken Hindi Audio│
│              ▼                                      │                  │
│  ┌──────────────────────────────────────────────────┴───────────────┐  │
│  │                   Conversation State Machine                     │  │
│  │    Stage 1: Fixed Sequential Hindi Baseline Interview            │  │
│  │    Stage 2: LangGraph Bounded Agentic Reasoning Loop (Max 6)     │  │
│  └───────────────────────────┬──────────────────────────────────────┘  │
│                              │                                         │
│                              ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │             Model Context Protocol (MCP) Statutory Tools         │  │
│  │                                                                  │  │
│  │  1. search_schemes(query, profile)                               │  │
│  │     └── Multilingual Embeddings + ChromaDB Vector Index          │  │
│  │                                                                  │  │
│  │  2. request_document(document_type)                              │  │
│  │     └── OpenCV Preprocessing (Deskew/Contrast) + Tesseract OCR  │  │
│  │                                                                  │  │
│  │  3. check_eligibility(profile, candidate_schemes)                │  │
│  │     └── DETERMINISTIC Python Rules Engine (Zero LLM In Verdicts) │  │
│  │                                                                  │  │
│  │  4. escalate_to_csc(reason)                                      │  │
│  │     └── Nearest Common Service Centre Contact & Geospatial Info  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   PostgreSQL Database & Storage                        │
│   • Schemes Table (JSONB criteria, benefits, fine-print conditions)   │
│   • Persistent ChromaDB Vector Store                                   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🏛️ Core Design Principles & Guardrails

1. **Deterministic Eligibility Verdicts**: The LLM agent **never** decides whether a citizen qualifies for a scheme. The verdict is calculated by plain, auditable Python logic comparing citizen profile attributes against official criteria.
2. **Model Context Protocol (MCP)**: Tools are exposed strictly via the official [Model Context Protocol](https://github.com/modelcontextprotocol/python-sdk), maintaining clear boundaries between the reasoning agent and data sources.
3. **Bounded Agent Trajectories**: The LangGraph orchestration loop is bounded to a maximum of 6 tool-call iterations per turn to guarantee predictable termination and eliminate infinite loops.
4. **Data Privacy & DPDP Act 2023 Compliance**: Zero third-party commercial APIs. Open-weight models only (Ollama/Llama/Mistral, Vasista Whisper, Indic-TTS). All testing uses synthetic mock documents.
5. **No TensorFlow/Keras**: Developed strictly with PyTorch, OpenCV, and classical ML tools per course guidelines.

---

## 📅 8-Phase Implementation Lifecycle

| Phase | Milestone | Key Artifacts & Modules |
|---|---|---|
| **Phase 1** | **Project Foundation** | Monorepo scaffolding, FastAPI `/health`, PostgreSQL Docker container, React Native CLI setup, `docs/architecture.md` |
| **Phase 2** | **Scheme Database** | `scrape_schemes.py`, data normalization, Alembic migrations, ChromaDB multilingual embeddings (`paraphrase-multilingual-mpnet-base-v2`) |
| **Phase 3** | **Baseline Interview** | Fixed 9-question Hindi baseline script in Devanagari, `ConversationManager` state machine, `test_interview_cli.py` |
| **Phase 4** | **Hindi STT & TTS** | `VasistaWhisperProvider` ASR, Indic-TTS audio synthesis, Word Error Rate (WER) test suite, `/stt` and `/tts` endpoints |
| **Phase 5** | **Agentic RAG Layer** | MCP tool definitions, LangGraph bounded reasoning loop (max 6 steps), Ollama integration, `test_agent_cli.py` |
| **Phase 6** | **Rules Engine & OCR** | Deterministic `EligibilityEngine` (`QUALIFIES`, `NEEDS_MORE_INFO`, `DOES_NOT_QUALIFY`), OpenCV + Tesseract OCR pipeline, 24 synthetic documents |
| **Phase 7** | **React Native App** | Native Android audio recorder (`AudioRecorderModule.kt`), conversational screens (Onboarding, Conversation, OCR, Results, CSC), SQLite offline queue |
| **Phase 8** | **Benchmarking & Report** | Comprehensive academic evaluation suite (ASR, Retrieval, Hallucination, OCR, Trajectory, End-to-End), final project report (`docs/`) |

---

## 📊 Academic Evaluation & Benchmark Results

Comprehensive benchmarking executed under Phase 8 across 6 independent evaluation suites:

| Benchmark Metric | Evaluated Target | Measured Result | Significance / Academic Note |
|---|---|---|---|
| **ASR Word Error Rate (WER)** | Baseline Spoken Hindi Queries | **12.4%** | Excellent intelligibility on demographic answers |
| **ASR Word Error Rate (WER)** | Open-Ended Stated Need Queries | **18.7%** | Handles domain-specific colloquial vocabulary |
| **Retrieval Top-1 Accuracy** | 35 Vernacular Ground Truth Pairs | **80.0%** | Relevant scheme identified as top candidate |
| **Retrieval Top-3 Accuracy** | 35 Vernacular Ground Truth Pairs | **94.3%** | High candidate recall before agent reasoning |
| **Retrieval Top-5 Accuracy** | 35 Vernacular Ground Truth Pairs | **97.1%** | Broad coverage across priority sectors |
| **Mean Reciprocal Rank (MRR)** | ChromaDB Vector Search | **0.864** | Ground truth scheme ranked in top 1–2 positions |
| **OCR Field Accuracy (Clean)** | Synthetic Indian Documents | **87.5%** | High fidelity on clean ration & income certificates |
| **OCR Field Accuracy (Degraded)**| Angled / Low-Light Camera Photos | **65.0%** | Real-world degradation gap characterized honestly |
| **Agent Trajectory Correctness** | Multi-Turn Complex Scenarios | **90.0%** | Follows proper search -> document -> rule sequence |
| **LLM Hallucination Rate** | Scheme Eligibility Claims | **0.0%** | Guaranteed by deterministic non-LLM eligibility engine |
| **End-to-End Task Success** | Start-to-Verifiable Spoken Result | **83.3%** | Complete conversation without premature escalation |

*Detailed benchmark breakdown and generated graphs are available in [`backend/evaluation/evaluation_results.md`](backend/evaluation/evaluation_results.md) and [`backend/evaluation/charts/`](backend/evaluation/charts/).*

---

## 🚀 Quickstart & Local Setup

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** and **npm**
- **Docker & Docker Compose**
- **Tesseract OCR** (`tesseract` and `tesseract-lang` with Hindi pack: `tesseract-ocr-hin`)
- **Android Studio** & Android SDK (API 34+) for mobile build

### 1. Backend & Database Setup
```bash
# Clone the repository
git clone https://github.com/Nikita-Gupta-19/YojanaVaani.git
cd YojanaVaani

# Start PostgreSQL service via Docker
docker compose up -d postgres

# Set up Python virtual environment
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Verify Backend Health
```bash
curl http://localhost:8000/health
# Response: {"status":"ok","database":"connected","timestamp":"..."}
```

### 3. Run Test Suites & CLI Verification
```bash
# Test conversational baseline interview in Hindi
python scripts/test_interview_cli.py

# Test deterministic rules engine & OCR pipeline
python scripts/test_eligibility_and_ocr.py

# Run comprehensive automated evaluations
cd evaluation
python generate_report.py
```

### 4. Mobile Client Setup (React Native)
```bash
cd ../mobile
npm install

# Start Metro bundler
npm start

# Run on connected Android device or emulator
npm run android
```

---

## 📁 Repository Directory Structure

```text
YojanaVaani/
├── AGENTS.md                          # Non-negotiable agentic coding constraints
├── docker-compose.yml                 # PostgreSQL & backend container configuration
├── Dataset.csv                        # Scraped & structured scheme dataset
├── docs/
│   ├── architecture.md                # System architectural blueprint
│   ├── specification.md               # Complete project specification
│   ├── data_quality_report.md         # Data extraction & auditing report
│   ├── major_project_report_ch1_to_ch4.md # B.Tech major project thesis report
│   └── screenshots/                   # Android UI walkthrough screenshots
├── backend/
│   ├── Dockerfile
│   ├── alembic/                       # PostgreSQL database migration versions
│   ├── app/
│   │   ├── api/                       # API routers (health, speech, documents, conversation)
│   │   ├── core/                      # Config settings & database session engine
│   │   ├── mcp/                       # Model Context Protocol tools implementation
│   │   ├── models/                    # SQLAlchemy & Pydantic models (Scheme, Conversation)
│   │   └── services/                  # ASR, TTS, LangGraph Agent, EligibilityEngine, OCR
│   ├── data/                          # Audio evaluation samples & synthetic mock documents
│   ├── evaluation/                    # 6-part academic benchmarking suite & charts
│   ├── scripts/                       # CLI interactive test harnesses
│   └── tests/                         # Pytest unit & integration test suite
├── data-pipeline/
│   ├── scrape_schemes.py              # myScheme.gov.in web scraper
│   ├── clean_and_preprocess.py        # Data normalization & extraction
│   ├── load_schemes.py                # PostgreSQL ingestion loader
│   ├── build_index.py                 # ChromaDB multilingual vector indexer
│   └── chroma_db/                     # Persistent ChromaDB vector database
└── mobile/
    ├── App.tsx                        # Root screen navigator & state orchestrator
    ├── src/
    │   ├── screens/                   # Onboarding, Conversation, Document, Results, CSC
    │   ├── services/                  # Audio recording & offline SQLite queue
    │   └── config.ts                  # Backend URL & network configuration
    └── android/                       # Native Android project with AudioRecorderModule.kt
```

---

## 📜 Academic Integrity & DPDP Act Compliance

This project was developed for the **B.Tech Major Project** curriculum.
- **Zero Real Identity Documents**: In accordance with the *Digital Personal Data Protection (DPDP) Act, 2023*, no real personal documents (Aadhaar cards, Ration cards, Income certificates) were collected or stored. All evaluation utilizes synthetic mock documents with dummy citizen names and registration IDs.
- **Open Science & Auditable ML**: All evaluation scripts report transparent, uncurated metrics, highlighting real-world challenges in rural ASR and degraded camera OCR.

---

## 👩‍💻 Author & Acknowledgements

- **Nikita Gupta** — B.Tech Computer Science and Engineering
- Guidance and support from Major Project faculty advisors and open-source models by AI4Bharat, HuggingFace, and LangChain communities.
