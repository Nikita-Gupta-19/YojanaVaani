# YojanaVaani — System Architecture Overview

## 1. System Overview

**YojanaVaani** is a voice-first native Android application designed to bridge the awareness and accessibility divide for government welfare schemes in India, specifically empowering rural and low-literacy citizens. The system operates entirely through spoken Hindi (Devanagari/regional dialects) and camera-assisted document verification.

```mermaid
graph TD
    User([Citizen / User]) <-->|Spoken Hindi & Camera| Mobile[React Native Mobile App<br/>Android Native Client]
    Mobile <-->|REST API / Audio / Multipart| Backend[FastAPI Backend Server]
    
    subgraph "Server-Side AI & Data Layer"
        Backend <--> Speech[Speech Engine<br/>Vasista22 / IndicWhisper STT<br/>Indic-TTS Synthesis]
        Backend <--> Agent[LangGraph Orchestration Agent<br/>Bounded Tool-Calling Loop]
        Backend <--> OCR[OpenCV + Tesseract OCR<br/>Hindi + English Field Extraction]
        
        Agent <-->|Model Context Protocol (MCP)| MCPTools[MCP Tool Suite]
        MCPTools <-->|search_schemes| VectorDB[(Chroma Vector DB<br/>paraphrase-multilingual-mpnet)]
        MCPTools <-->|check_eligibility| RuleEngine[Deterministic Rules Engine<br/>Python Rule Evaluator]
        MCPTools <-->|request_document| OCR
        MCPTools <-->|escalate_to_csc| CSCService[Common Service Centre Locator]
        
        Backend <--> Postgres[(PostgreSQL Database<br/>Schemes, Profiles, Sessions)]
    end
```

## 2. Core Architectural Principle: Thin Client, Server-Side AI

**All AI inference runs strictly server-side.**
- The React Native mobile application is a lightweight client responsible solely for:
  1. Audio recording and streaming / playback.
  2. Camera capture for identity/income documents.
  3. Clean, high-contrast, accessible visual presentation for users who can read secondary cues.
  4. Local SQLite queuing for unreliable or intermittent network connectivity.
- Under no circumstances does the mobile app perform STT, TTS, RAG vector searches, OCR processing, or LLM reasoning locally. This preserves battery life, keeps the APK lightweight, and ensures high-quality inference using dedicated server compute.

## 3. Two-Stage Conversational Flow

1. **Stage 1: Fixed Baseline Interview**:
   - A structured, scripted interview in spoken Hindi covering vital demographic fields: name, age, gender, state/district, approximate income bracket, social category, occupation, disability status, and stated need.
   - Fixed ordering ensures predictability, data completeness, and zero LLM hallucination during profile capture.
2. **Stage 2: Agentic Follow-up Loop (LangGraph & MCP)**:
   - Once baseline is complete, control passes to a LangGraph orchestration agent.
   - The agent is equipped with exactly four MCP tools:
     - `search_schemes(query, profile)`: Vector search over scraped schemes.
     - `request_document(document_type)`: Triggers photo capture and OCR extraction.
     - `check_eligibility(profile, candidate_schemes)`: **Deterministic, rule-based Python logic (NEVER an LLM decision)**.
     - `escalate_to_csc(reason)`: Locates the nearest physical Common Service Centre if unresolvable.
   - Hard bounded at a maximum of 6 tool-call iterations per conversational turn to prevent runaway loops.

## 4. Technology Stack & Component Mapping

| Layer | Technology | Rationale / Constraints |
|---|---|---|
| **Mobile Client** | React Native (TypeScript), React Native CLI | Native Android camera/mic module access, no Expo managed workflow |
| **Backend API** | FastAPI, SQLAlchemy, Uvicorn | High-performance asynchronous API, Python ecosystem integration |
| **Relational Database** | PostgreSQL 16 | Relational scheme catalog, semi-structured JSONB eligibility criteria |
| **Vector Database** | Chroma | Multilingual scheme embedding and semantic similarity matching |
| **Embeddings** | `paraphrase-multilingual-mpnet-base-v2` | PyTorch-based multilingual representation for Hindi/English queries |
| **Speech-to-Text (STT)** | Vasista22 Whisper / IndicWhisper | Fine-tuned for Indian accents and spoken Hindi |
| **Text-to-Speech (TTS)** | AI4Bharat Indic-TTS / IndicF5 | Clear, natural spoken Hindi audio generation |
| **OCR** | Tesseract (pytesseract) + OpenCV | Hindi & English optical character recognition for documents |
| **Orchestration** | LangGraph + MCP (Model Context Protocol) | Bounded tool-calling agent with strict protocol isolation |
| **Containerization** | Docker, Docker Compose | Reproducible development, automated service orchestration |

*Forbidden in codebase:* TensorFlow, Keras, Matlab (Course institutional rule — PyTorch/classical-ML utilized throughout).
