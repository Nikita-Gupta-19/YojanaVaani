# YOJANAVAANI (योजना वाणी)
## An Agentic Voice-First Multimodal AI System for Vernacular Welfare Scheme Discovery and Deterministic Eligibility Verification

---

**MAJOR PROJECT INTERIM REPORT (CHAPTERS 1 TO 4)**

*Submitted in partial fulfillment of the requirements for the degree of*  
**Bachelor of Technology in Computer Science & Engineering**

---

## TABLE OF CONTENTS

- **Chapter 1: Introduction**
  - 1.1 Background
  - 1.2 Problem Statement
  - 1.3 Social & Environmental Relevance
  - 1.4 Gantt Chart / Project Timeline
  - 1.5 Scope of the Project
- **Chapter 2: Literature Survey / Critical Review**
  - 2.1 Overview of Existing Work & Dataset Study
  - 2.2 Summary Comparison Table
  - 2.3 Research Gaps, Citizen Awareness Deficit Analysis, & Project Contribution
- **Chapter 3: System Design & Methodology**
  - 3.1 Proposed Methodology & Architectural Block Diagrams
  - 3.2 Tool and Technique Selection Justifications
- **Chapter 4: Implementation & Testing**
  - 4.1 Experimental Setup
  - 4.2 Test Cases, Case Study Walkthrough, & Next Steps Implementation Roadmap

---

# CHAPTER 1: INTRODUCTION

## 1.1 Background
The Government of India and various state governments administer more than 2,300 welfare schemes and direct benefit transfers designed to uplift marginalized, rural, and economically weaker sections of society. These programs encompass social security pensions, agricultural equipment and credit subsidies, maternal healthcare nutrition supplements, housing grants, educational scholarships, and life/disability insurance covers. Significant flagship initiatives include the *Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)*, *Pradhan Mantri Awas Yojana (PMAY)*, *Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (PM-JAY)*, and the *National Social Assistance Programme (NSAP)*.

Despite substantial budgetary allocations exceeding ₹4.5 lakh crore annually across social sectors, a profound "last-mile delivery deficit" persists. The primary barrier preventing rightful beneficiaries from claiming these benefits is not an absence of government funding, but a severe discoverability and access bottleneck. The target beneficiaries—predominantly smallholder farmers, landless daily wage laborers, elderly rural citizens, and economically backward families—frequently lack formal literacy, digital proficiency, and institutional access. They operate within an oral, vernacular linguistic paradigm, speaking regional dialects of Hindi rather than standard English or high-register official Hindi.

The conventional digitization of government schemes through national portals (such as *myScheme.gov.in*, *UMANG*, and state-specific portals) has transitioned paper bureaucracies into web interfaces. However, web interfaces implicitly require:
1. Ownership of desktop or modern smartphone devices with high-speed internet.
2. High levels of textual literacy and comprehension of dense bureaucratic legal jargon.
3. Complex multi-step filtering by exact administrative categorization (caste categories, sub-castes, land area units like bigha/acre, official income slabs).

As a direct consequence, rural citizens are forced to depend upon informal village intermediaries, unaccredited brokers, and local cyber-café operators who routinely charge exploitative commissions or misinform citizens regarding eligibility criteria. *YojanaVaani* addresses this systemic inequity by developing an agentic, voice-first, native mobile application that allows rural citizens to discover, verify, and document their eligibility for public welfare schemes entirely through spoken vernacular Hindi.

## 1.2 Problem Statement
Existing welfare delivery systems suffer from three fundamental technical and structural challenges:

1. **Linguistic and Modality Exclusion**: Current public portals are predominantly text-centric and English/formal Hindi-based. There is an absence of intuitive, voice-first conversational interfaces capable of understanding conversational Hindi with regional rural accents, code-mixed dialects, and informal phrasing.
2. **LLM Hallucination and Absence of Auditable Determinism**: Emerging generative AI chatbots (such as standard OpenAI GPT-4 wrappers or conversational pilots) utilize large language models to directly answer citizen eligibility queries. In high-stakes public governance, LLMs frequently hallucinate eligibility requirements, invent non-existent benefits, overlook statutory income ceilings, or offer conflicting verdicts. An algorithmic error in governance can lead to catastrophic legal and economic denial of entitlements.
3. **Complex Documentation and Multimodal Burden**: Ascertaining eligibility requires evaluating citizen identity and economic credentials (e.g., Aadhaar cards, BPL ration cards, land revenue records, disability certificates, income affidavits). Citizens frequently struggle to interpret whether their existing documents fulfill complex statutory rules.

Therefore, the objective of this project is:
> *"To design, implement, and empirically evaluate **YojanaVaani**, a voice-first native mobile application powered by an agentic backend orchestration framework that decouples probabilistic conversational understanding (via speech recognition, multilingual vector retrieval, and bounded LLM agent orchestration) from deterministic, rule-based eligibility verification, guaranteeing 100% auditability and zero hallucination in public welfare delivery."*

## 1.3 Social & Environmental Relevance

### 1.3.1 Social Relevance
- **Democratization of Welfare Access**: By eliminating the textual literacy barrier, YojanaVaani empowers millions of rural, illiterate, and semi-literate citizens to directly interact with social welfare registries in their mother tongue.
- **Elimination of Exploitative Intermediaries**: Middlemen frequently extract 10% to 30% of direct benefit grants or charge ₹200–₹500 per inquiry simply to look up schemes. A transparent, automated, zero-cost voice advisor restores citizen agency and preserves hard-earned entitlements.
- **Gender and Disability Inclusion**: Rural women and Persons with Disabilities (PwDs) face significant mobility constraints. YojanaVaani provides an accessible voice and camera interface directly on a low-cost smartphone, enabling home-based self-screening.
- **Statutory Compliance with DPDP Act 2023**: In alignment with India's *Digital Personal Data Protection (DPDP) Act, 2023*, the system operates under strict data minimization and purpose limitation principles. Citizen voice recordings and document scans are processed on secure private infrastructure with zero transmission to commercial third-party APIs.

### 1.3.2 Environmental Relevance
- **Paperless Administration**: Welfare eligibility inquiries traditionally consume massive amounts of physical documentation, photocopies, notarized affidavits, and physical paper pamphlets. Multimodal digital capture and local OCR eliminate redundant paper consumption.
- **Decarbonization of Citizen Commuting**: Rural citizens routinely travel between 15 km to 50 km to block development offices (Tehsil) or district headquarters multiple times merely to ascertain required documents or scheme status. By providing definitive eligibility verdicts and exact document requirements locally, YojanaVaani drastically curtails physical vehicular commuting, reducing rural transport emissions.

## 1.4 Gantt Chart / Timeline
The project is structured across an 8-phase developmental lifecycle spanning 16 academic weeks. Table 1.1 delineates the project timeline, milestones, and deliverables.

```
+---------------------------------------------------------------------------------------------------------+
|                                      PROJECT GANTT CHART (WEEKS 1 - 16)                                 |
+-------------------+---+---+---+---+---+---+---+---+---+----+----+----+----+----+----+----+----------------+
| Phase / Milestone | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | Status         |
+-------------------+---+---+---+---+---+---+---+---+---+----+----+----+----+----+----+----+----------------+
| Phase 1: Inception|===|   |   |   |   |   |   |   |   |    |    |    |    |    |    |    | Completed      |
| Phase 2: Corpus/DB|   |===|===|===|   |   |   |   |   |    |    |    |    |    |    |    | Completed      |
| Phase 3: Rules Eng|   |   |   |   |===|===|   |   |   |    |    |    |    |    |    |    | Current Stage  |
| Phase 4: Voice STT|   |   |   |   |   |   |===|===|   |    |    |    |    |    |    |    | Next Step      |
| Phase 5: MCP/Agent|   |   |   |   |   |   |   |   |===|=== |    |    |    |    |    |    | Planned        |
| Phase 6: Mobile App|  |   |   |   |   |   |   |   |   |    |=== |=== |    |    |    |    | Planned        |
| Phase 7: OCR Pipe |   |   |   |   |   |   |   |   |   |    |    |    |=== |=== |    |    | Planned        |
| Phase 8: Eval/Rep |   |   |   |   |   |   |   |   |   |    |    |    |    |    |=== |=== | Planned        |
+-------------------+---+---+---+---+---+---+---+---+---+----+----+----+----+----+----+----+----------------+
```
*Table 1.1: Academic Major Project Phased Lifecycle Timeline.*

- **Phase 1 (Weeks 1–2)**: Problem definition, institutional constraints analysis, ethics/privacy review.
- **Phase 2 (Weeks 3–5)**: Data pipeline construction, scraping of myScheme corpus, schema normalization, vector indexing, and database inconsistency remediation.
- **Phase 3 (Weeks 6–7)**: Mathematical modeling and deterministic rules engine development (`check_eligibility`).
- **Phase 4 (Weeks 8–9)**: Speech-to-Text (IndicWhisper) and Text-to-Speech (Indic-TTS) voice pipeline deployment.
- **Phase 5 (Weeks 10–11)**: Model Context Protocol (MCP) server creation and LangGraph agentic orchestration loop.
- **Phase 6 (Weeks 12–13)**: React Native native Android mobile application frontend integration.
- **Phase 7 (Weeks 14–15)**: Multimodal document acquisition, OpenCV image deskewing, and Tesseract OCR integration.
- **Phase 8 (Week 16)**: End-to-end latency, precision-recall evaluation, CSC fallback audit, and final dissertation report.

## 1.5 Scope of the Project

### 1.5.1 In-Scope Functionality
1. **Curated Multi-Sector Scheme Corpus**: 270 central and state government welfare schemes spanning Central Government, Delhi NCT, and Uttar Pradesh across 9 critical sectors (Agriculture, Education, Health, Housing, Women & Child Development, Social Welfare, Pensions, Urban Development, Labour).
2. **Bilingual Conversational Interface**: Native spoken Hindi speech recognition and natural Hindi speech synthesis.
3. **Structured Two-Stage Dialogue**:
   - *Stage 1*: Fixed scripted 9-question baseline interview gathering fundamental profile facts (Name, Age, Gender, State/District, Social Category, Occupation, Annual Income, Disability Status, Core Need).
   - *Stage 2*: Dynamic, bounded LangGraph agentic follow-up loop (maximum 6 iterations per conversational turn).
4. **Decoupled Architecture with Exactly Four MCP Tools**:
   - `search_schemes(query, profile)`: Semantic vector retrieval over ChromaDB.
   - `request_document(document_type)`: Multimodal document capture and OCR extraction.
   - `check_eligibility(profile, candidate_schemes)`: 100% deterministic Python rules engine.
   - `escalate_to_csc(reason)`: Graceful human handoff to nearest Common Service Centre.
5. **Native Android Client**: Lightweight React Native Android APK with offline action queuing via SQLite.

### 1.5.2 Out-of-Scope Functionality
1. **End-to-End Government Application Submission**: Direct write access to proprietary government databases (e.g., submitting an application directly into the PFMS or state portal) requires bilateral ministry memorandum of understanding (MoU) and API tokens unavailable for academic research.
2. **All-India 2,300+ Scheme Corpus**: Indexing every municipal and state-level scheme across all 28 states and 8 union territories is out of scope for a single-semester major project.
3. **Forensic Physical Document Authentication**: Verifying whether a submitted Aadhaar or Ration Card is counterfeit requires central UIDAI biometric authentication servers.

---

# CHAPTER 2: LITERATURE SURVEY / CRITICAL REVIEW

## 2.1 Overview of Existing Work & Dataset Study

### 2.1.1 Overview of Existing Work
Extensive research has addressed information retrieval in e-governance and accessibility for low-literacy populations:
1. **National Public Service Portals (*myScheme.gov.in*, *UMANG*)**: Launched by the Ministry of Electronics and Information Technology (MeitY) and the National Informatics Centre (NIC), myScheme aggregates central and state schemes. While comprehensive, the portal functions as an electronic catalog requiring multi-attribute filtering. Studies by *Gupta et al. (2022)* highlight that over 74% of rural respondents fail to complete a scheme discovery session without manual assistance due to terminology mismatches.
2. **Generative Voice Assistants (*Jugalbandi*)**: Developed by AI4Bharat, OpenNyAI, and Microsoft, *Jugalbandi* pioneered WhatsApp-based voice bots utilizing OpenAI large language models. However, field reports indicate a critical vulnerability: when queried regarding nuanced eligibility criteria, generative models produce hallucinations, misquoting age thresholds or assuring citizens of cash subsidies for which they do not qualify.
3. **Speech Interfaces for Low-Literacy Populations**: Seminal works by *Medhi et al. (2007)* and *Patel et al. (2010)* established that voice-first and multimodal visual cues reduce user error rates by over 80% compared to pure text among rural Indian populations. Recent advances in Indic speech recognition (*AI4Bharat IndicWhisper, 2023*) have enabled low-resource Indian language transcription at Word Error Rates (WER) below 18%.

### 2.1.2 Schemes Studied for Dataset (Corpus Analysis)
To ground YojanaVaani in real-world governance, a comprehensive dataset of **270 schemes** was scraped, cleaned, normalized, and indexed from *myScheme.gov.in*. The corpus is rigorously balanced across Central, Delhi, and Uttar Pradesh jurisdictions spanning 9 functional domains.

```
+------------------------------------+----------------+--------------------+
| Sector / Category                  | Scheme Count   | Percentage (%)     |
+------------------------------------+----------------+--------------------+
| Social Welfare & Empowerment       | 68             | 25.19%             |
| Education & Scholarships           | 52             | 19.26%             |
| Agriculture & Rural Livelihoods    | 39             | 14.44%             |
| Women and Child Development        | 31             | 11.48%             |
| Healthcare & Medical Relief        | 27             | 10.00%             |
| Housing & Urban Development        | 19             | 7.04%              |
| Employment, Skilling & Labour      | 15             | 5.56%              |
| Pensions & Senior Citizen Support  | 11             | 4.07%              |
| Financial Inclusion & Insurance    | 8              | 2.96%              |
+------------------------------------+----------------+--------------------+
| Total Verified Scheme Dataset      | 270            | 100.00%            |
+------------------------------------+----------------+--------------------+
```
*Table 2.1: Distribution of Studied Schemes across Functional Sectors.*

Key characteristics extracted and normalized in the schema include:
- **Age Constraints**: 108 schemes enforce hard statutory age boundaries (e.g., 18–40 years for *Pradhan Mantri Shram Yogi Maan-dhan*, 60+ years for *Indira Gandhi National Old Age Pension*).
- **Income Ceilings**: 87 schemes enforce explicit annual family income ceilings (ranging from ₹24,000/year for rural widow pensions to ₹8,00,000/year for post-matric scholarships).
- **Social Stratification**: 62 schemes have explicit caste quotas (SC, ST, OBC, Minority, General).
- **Gender Exclusivity**: 37 schemes specifically target women or adolescent girls.
- **Disability Provisions**: 11 schemes specifically target Persons with Disabilities ($\ge 40\%$ benchmark disability).

## 2.2 Summary Comparison Table

| Feature / Dimension | Official Portals (myScheme, UMANG) | Generative LLM Bots (Jugalbandi, ChatGPT) | Rule-Based Expert Systems | **YojanaVaani (Proposed System)** |
|:---|:---|:---|:---|:---|
| **Primary Interaction Modality** | Desktop/Mobile Text Input | Text / Speech-to-Text | Structured Form Fields | **Voice-First Spoken Vernacular Hindi** |
| **Eligibility Verification** | Manual citizen reading & self-selection | Pure Generative LLM (Hallucination-prone) | Hardcoded rule logic | **Deterministic Python Rules Engine (0% Hallucination)** |
| **Architectural Design** | Monolithic Web App | Single LLM Prompt Chain | Monolithic Script | **Agentic Orchestration (LangGraph + MCP SDK)** |
| **Conversational Structure** | None (Static Navigation) | Free-form Unbounded Chat | Rigid Static Form Wizard | **Two-Stage: Fixed Baseline + Bounded Tool-Use Agent** |
| **Document Intake & OCR** | Manual PDF upload | Unprocessed image upload | None | **Multimodal OpenCV Preprocessing + Local Tesseract OCR** |
| **Offline Resilience** | Inoperable without internet | Inoperable without internet | Local DB only | **Local SQLite Action & Audio Queueing** |
| **Failure Mode Handling** | Dead-end error page | Hallucinated advice or silent failure | Rejection alert | **Deterministic `escalate_to_csc` with exact rationale** |
| **Privacy & DPDP Compliance** | Central Cloud Logging | Commercial Third-Party APIs (OpenAI) | Local Server | **On-premise / Local Open-Weight Models, Zero Third-Party Leak** |

*Table 2.2: Comprehensive Architectural and Functional Comparison Matrix.*

## 2.3 Research Gaps, Citizen Awareness Deficit Analysis, & Project Contribution

### 2.3.1 Real-Life Citizen Awareness Deficit
Extensive empirical data from the National Sample Survey Office (NSSO 75th and 78th Rounds on Social Consumption) and NITI Aayog policy evaluations reveal a staggering awareness deficit in rural India:
- **60% to 75%** of eligible rural households do not avail of welfare schemes for which they meet all statutory criteria.
- In social security insurance (*PMSBY*, *PMJJBY*), despite automated bank enrollment, over **68%** of rural nominees are unaware of the claim procedure upon accidental death or disability.
- In agricultural welfare (*PM-KISAN*), while national coverage is high, over **34%** of eligible tenant and female farmers remain excluded due to land-record documentation ambiguities.
- In educational scholarships (*Pre-Matric & Post-Matric SC/ST/OBC Scholarships*), over **52%** of low-income rural students miss application deadlines due to lack of timely knowledge regarding domicile and income certificate formats.

The four primary causal drivers of this deficit are:
1. **The Literacy-Jargon Chasm**: Legal gazette notifications use archaic bureaucratic Hindi (e.g., *"अधिप्रमाणित शपथ पत्र"*, *"सक्षम प्राधिकारी द्वारा निर्गत आय प्रमाण पत्र"*) which rural citizens cannot comprehend.
2. **The Document Discovery Barrier**: Citizens do not know *which* specific certificate proves a criterion (e.g., confusing a BPL Ration Card with an Income Certificate).
3. **Information Fragmentation**: Central schemes, state matching funds, and district initiatives are hosted on disconnected websites.
4. **Lack of Local Accountability**: When an application fails, citizens are rarely given the precise statutory disqualification reason.

### 2.3.2 How YojanaVaani Solves These Gaps
YojanaVaani provides an auditable, compassionate, and technically robust solution:
1. **Vernacular Acoustic Accessibility**: The citizen simply speaks naturally (e.g., *"मैं सीतापुर का किसान हूँ, दो बीघा जमीन है, कोई योजना है क्या?"*). The system transcribes, extracts entity facts, and queries the knowledge base without demanding portal literacy.
2. **Guaranteed Eligibility Integrity**: By isolating LLM reasoning to tool invocation and delegating eligibility calculation to deterministic code, YojanaVaani guarantees that every positive or negative verdict is mathematically defensible and explainable.
3. **Automated Document Guidance**: Through `request_document`, the system inspects the citizen's document via computer vision, verifies validity periods and issuing authorities, and extracts required field numbers.
4. **Actionable CSC Bridge**: When document extraction fails or physical verification is mandatory, the system generates a concise referral summary for the local Common Service Centre (*VLE - Village Level Entrepreneur*), bridging the digital-physical divide.

---

# CHAPTER 3: SYSTEM DESIGN & METHODOLOGY

## 3.1 Proposed Methodology & Architectural Block Diagrams

### 3.1.1 Architectural Overview
YojanaVaani is architected as a decoupled, multi-tier agentic system adhering to clean separation of concerns. Figure 3.1 illustrates the end-to-end system topology.

```
+---------------------------------------------------------------------------------------------------+
|                                      SYSTEM TOPOLOGY ARCHITECTURE                                 |
+---------------------------------------------------------------------------------------------------+
|  CLIENT TIER (Mobile App - React Native Android CLI)                                              |
|  [ Microphone / Audio Capture ]  [ Camera / Doc Intake ]  [ Audio Player ]  [ SQLite Local Queue ] |
+-------------------------------------------------+-------------------------------------------------+
                                                  | HTTP / Multipart REST API
                                                  v
+---------------------------------------------------------------------------------------------------+
|  BACKEND API GATEWAY (FastAPI / Asynchronous Python 3.11)                                         |
|  [ Audio Encoding Middleware ]  [ Session State Manager ]  [ DPDP Privacy & Redaction Guard ]     |
+-----------------------------------+-----------------------------+---------------------------------+
                                    |                             |
                                    v                             v
+-----------------------------------+---+  +---------------------+---------------------------------+
| VOICE PROCESSING TIER                 |  | OCR & DOCUMENT VISION TIER                             |
| - STT: AI4Bharat IndicWhisper         |  | - OpenCV Preprocessing (Deskew, Contrast, Grayscale)  |
| - TTS: AI4Bharat Indic-TTS            |  | - Tesseract OCR (Devanagari 'hin' + 'eng' packs)       |
+-----------------------------------+---+  +---------------------+---------------------------------+
                                    |                             |
                                    +--------------+--------------+
                                                   |
                                                   v
+---------------------------------------------------------------------------------------------------+
|  AGENTIC ORCHESTRATION TIER (LangGraph State Machine)                                             |
|  - Bounded Loop (Max 6 Iterations)                                                                |
|  - Reasoning Engine: Local Open-Weight LLM (Llama-3 / Mistral via Ollama)                        |
|  - Model Context Protocol (MCP) Official Python SDK Client Interface                              |
+--------------------------------------------------+------------------------------------------------+
                                                   | Protocol Invocations
                                                   v
+---------------------------------------------------------------------------------------------------+
|  STANDARDIZED MCP TOOL SERVER (4 Bounded Statutory Tools)                                         |
|                                                                                                   |
|  1. search_schemes(query, profile)          2. request_document(document_type)                    |
|     --> ChromaDB Multilingual Vector Store     --> Multimodal Document Parser                     |
|                                                                                                   |
|  3. check_eligibility(profile, candidates)  4. escalate_to_csc(reason)                            |
|     --> 100% Deterministic Python Rules        --> Geo-Spatial CSC Locator & Referral Ticket       |
+--------------------------------------------------+------------------------------------------------+
                                                   |
                                                   v
+---------------------------------------------------------------------------------------------------+
|  PERSISTENCE TIER (PostgreSQL 15 + ChromaDB)                                                      |
|  - Relational: 270 Normalized Schemes, Income Tiers, Caste, Age Constraints, Document Schemas      |
|  - Vector Store: Multilingual Embeddings ('paraphrase-multilingual-mpnet-base-v2')               |
+---------------------------------------------------------------------------------------------------+
```
*Figure 3.1: YojanaVaani System Topology Block Diagram.*

### 3.1.2 Two-Stage Conversational Flowchart
To optimize computational efficiency and avoid open-ended prompt drift, citizen interactions follow a rigorous two-stage state machine (Figure 3.2).

```
                      +-----------------------------+
                      | Citizen Initiates Session   |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | STAGE 1: Baseline Interview |
                      | (9 Fixed Scripted Questions)|
                      +--------------+--------------+
                                     |
                 +-------------------+-------------------+
                 | 1. Name           4. State / District |
                 | 2. Age            5. Income Tier      |
                 | 3. Gender         6. Social Category  |
                 | 7. Occupation     8. Disability Status|
                 | 9. Core Need / Assistance Sought      |
                 +-------------------+-------------------+
                                     |
                                     v
                      +-----------------------------+
                      | Citizen Profile Fact Sheet  |
                      | Instantiated in Memory      |
                      +--------------+--------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
| STAGE 2: Bounded LangGraph Agentic Follow-Up Loop (Max 6 Iterations)     |
|                                                                         |
|            +-----------------------------------------------+            |
|            | LLM Evaluates State & Citizen Query Context   |            |
|            +-----------------------+-----------------------+            |
|                                    |                                    |
|             +----------------------+----------------------+             |
|             | Decides Next Tool Action (MCP Protocol)     |             |
|             +---+--------------+--------------+-------+---+             |
|                 |              |              |       |                 |
|                 v              v              v       v                 |
|          search_schemes  check_elig  request_doc  escalate_csc          |
|                 |              |              |       |                 |
|                 +--------------+--------------+-------+                 |
|                                |                                        |
|                                v                                        |
|            +-----------------------------------------------+            |
|            | Bounded Check: Iteration < 6?                 |            |
|            +-----------------------+-----------------------+            |
|                                    |                                    |
|                    +---------------+---------------+                    |
|                    | YES                           | NO (Exceeded Limit)|
|                    v                               v                    |
|            Evaluate Next Step               Force Escalate              |
|            or Formulate Final               to CSC with                 |
|            Hindi Voice Response             Session Summary             |
+------------------------------------+------------------------------------+
                                     |
                                     v
                      +-----------------------------+
                      | Synthesize Audio (Indic-TTS)|
                      | Stream Playback to Mobile   |
                      +-----------------------------+
```
*Figure 3.2: State Transition Flowchart of Two-Stage Conversational Pipeline.*

### 3.1.3 Deterministic Eligibility Mathematical Model
The rules engine evaluates candidate schemes against citizen profile facts using boolean predicate logic. For a citizen profile $P = \{age, income, gender, state, category, disability, occupation\}$ and a candidate scheme $S$:

$$Eligible(P, S) = \Psi_{age}(P, S) \wedge \Psi_{income}(P, S) \wedge \Psi_{state}(P, S) \wedge \Psi_{gender}(P, S) \wedge \Psi_{caste}(P, S) \wedge \Psi_{disability}(P, S)$$

Where each statutory predicate is evaluated deterministically:
- $\Psi_{age}(P, S) = (S.min\_age \le P.age \le S.max\_age) \cup (S.age\_bounds = \emptyset)$
- $\Psi_{income}(P, S) = (P.income \le S.income\_ceiling) \cup (S.income\_ceiling = \emptyset)$
- $\Psi_{state}(P, S) = (P.state \in S.applicable\_states) \cup ('All' \in S.applicable\_states)$
- $\Psi_{gender}(P, S) = (P.gender == S.target\_gender) \cup ('All' \in S.target\_gender)$
- $\Psi_{caste}(P, S) = (P.category \in S.eligible\_categories) \cup ('All' \in S.eligible\_categories)$
- $\Psi_{disability}(P, S) = (P.disability == True \text{ if } S.is\_pwd\_only \text{ else } True)$

If any statutory predicate evaluates to $False$, the scheme is conclusively flagged as $Ineligible$ with the exact failing criterion recorded for citizen auditability.

## 3.2 Tool and Technique Selection Justifications

```
+--------------------------+------------------------------+---------------------------------------------------------------------------------+
| Architectural Layer      | Selected Technology          | Technical Justification & Selection Rationale                                    |
+--------------------------+------------------------------+---------------------------------------------------------------------------------+
| Mobile Client Framework  | React Native CLI (TypeScript)| Selected over Expo and Flutter. React Native CLI compiles to a lightweight,     |
|                          |                              | native Android APK with direct access to Android audio buffers and camera HAL.  |
|                          |                              | Avoids Expo managed workflow bloat and third-party dependency locks.            |
+--------------------------+------------------------------+---------------------------------------------------------------------------------+
| Backend Web Server       | FastAPI (Python 3.11)        | Selected over Flask and Django. Provides native ASGI asynchronous high-         |
|                          |                              | concurrency, automatic OpenAPI documentation, and strict Pydantic data schemas. |
+--------------------------+------------------------------+---------------------------------------------------------------------------------+
| Speech-to-Text (STT)     | AI4Bharat IndicWhisper       | Selected over OpenAI Whisper. IndicWhisper is specifically fine-tuned on over   |
|                          | (fallback: vasista22 Whisper)| 20,000 hours of Indian vernacular speech, delivering significantly lower WER    |
|                          |                              | on accented rural Hindi and code-switched phrases.                             |
+--------------------------+------------------------------+---------------------------------------------------------------------------------+
| Text-to-Speech (TTS)     | AI4Bharat Indic-TTS          | Selected over Google Cloud TTS. Open-source, low-latency, and reproduces       |
|                          |                              | authentic regional Hindi phonetic inflection without commercial API egress fees.|
+--------------------------+------------------------------+---------------------------------------------------------------------------------+
| Vector Embeddings        | paraphrase-multilingual-     | Generates 768-dimensional dense embeddings aligned across Hindi and English.   |
|                          | mpnet-base-v2 (Sentence-Xfrm)| Enables semantic matching between colloquial Hindi queries and official gazettes|
+--------------------------+------------------------------+---------------------------------------------------------------------------------+
| Vector Database          | ChromaDB                     | Lightweight, embeddable vector database that runs entirely in-process/local     |
|                          |                              | Docker container. Avoids complex distributed cloud infrastructure overhead.    |
+--------------------------+------------------------------+---------------------------------------------------------------------------------+
| Agent Orchestration      | LangGraph                    | Selected over linear LangChain and AutoGen. Implements cyclic state machines    |
|                          |                              | with hard bounds (max 6 iterations), strict state transitions, and checkpoints. |
+--------------------------+------------------------------+---------------------------------------------------------------------------------+
| Tool Protocol Interface  | Model Context Protocol (MCP) | Official Python SDK protocol standardizes tool discovery, execution boundaries, |
|                          | (Anthropic MCP SDK)          | and security sandboxing between the reasoning agent and underlying services.    |
+--------------------------+------------------------------+---------------------------------------------------------------------------------+
| Relational Storage       | PostgreSQL 15 + SQLAlchemy   | ACID-compliant storage for normalized schemes, relational foreign keys,         |
|                          |                              | citizen session logs, and multi-field indexing.                                |
+--------------------------+------------------------------+---------------------------------------------------------------------------------+
| OCR & Document Vision    | Tesseract OCR + OpenCV       | Local OpenCV preprocessing (deskewing, adaptive binarization) combined with     |
|                          | (pytesseract 'hin'+'eng')    | Devanagari Tesseract language pack guarantees zero cloud leak of identity data. |
+--------------------------+------------------------------+---------------------------------------------------------------------------------+
```
*Table 3.1: Comprehensive Technology Selection Justification Matrix.*

---

# CHAPTER 4: IMPLEMENTATION & TESTING

## 4.1 Experimental Setup

### 4.1.1 Hardware Specifications
- **Workstation Development Environment**: Apple Silicon Mac (M-Series / 16 GB Unified Memory) and Ubuntu 22.04 LTS Server environment.
- **Compute Acceleration**: PyTorch MPS (Metal Performance Shaders) / CUDA 12.1 acceleration for local transformer embeddings and acoustic feature extraction.
- **Testing Physical Device**: Android Smartphone running Android 13 (API Level 33), 4 GB RAM, 6.5-inch touch display, integrated microphone and 13MP camera sensor.

### 4.1.2 Software Specifications and Environment Dependencies
- **Core Runtime**: Python 3.11.9, Node.js v20.x, React Native CLI 0.73+.
- **Primary Libraries**:
  - `fastapi==0.110.0`, `uvicorn==0.28.0`, `pydantic==2.6.4`
  - `sqlalchemy==2.0.28`, `psycopg2-binary==2.9.9`
  - `chromadb==0.4.24`, `sentence-transformers==2.5.1`
  - `langgraph==0.0.26`, `langchain==0.1.11`, `mcp==0.1.0`
  - `torch==2.2.1`, `torchaudio==2.2.1`
  - `opencv-python-headless==4.9.0.80`, `pytesseract==0.3.10`
- **Zero-Tolerance Prohibited Frameworks**: In strict accordance with institutional BTech academic regulations, **TensorFlow, Keras, and MATLAB are 100% excluded** from all codebases, virtual environments, and sub-dependencies.

### 4.1.3 Database and Corpus Preprocessing Implementation
The database was established through an automated data pipeline (`data-pipeline/clean_and_preprocess.py`) importing into PostgreSQL and ChromaDB. During comprehensive quality audits, several subtle data anomalies were systematically identified and remediated:
1. **Canonical State Restriction Alignment**: 99 schemes exhibited state mismatches between textual tags and filter fields. All rows were normalized into canonical arrays (`['Delhi']`, `['Uttar Pradesh']`, `['All']`). Contradictions (such as Delhi University internships marked as Pan-India) were resolved to `None`.
2. **Cycle-Free Scheme Hierarchy**: 4 circular self-referencing foreign keys (`parent_scheme_id` pointing to own `id` in schemes 57, 424, 571, 595) were identified and eliminated.
3. **Structured Document Deserialization**: 262 rows with corrupted string-escaped nested JSON strings (`[["['[\\'...`) were completely deserialized into valid `DocumentRequirement` objects, ensuring document types, mandatory flags, and validity periods are machine-readable.
4. **Income Ceiling and Age Bound Recovery**: Automated regex extraction was augmented with verified prose parsing, expanding explicit numerical income ceilings to 87 schemes and age constraints to 108 schemes with zero drift.
5. **Confidence Score Calibration**: An empirical audit formula verified all 270 schemes, achieving a **mean database quality score of 0.990**, with 95.2% of schemes scoring $\ge 0.85$.

## 4.2 Test Cases, Case Study Walkthrough, & Next Steps Implementation Roadmap

### 4.2.1 Phase 1 & 2 Automated Test Suite
To verify the integrity of the completed corpus and data tier, automated verification scripts were executed. Table 4.1 documents the verified test suites.

```
+--------------------+---------------------------------------------------+--------------------+----------+
| Test ID            | Verification Scope / Target Logic                 | Expected Output    | Status   |
+--------------------+---------------------------------------------------+--------------------+----------+
| TC-DB-01           | PostgreSQL Record Count & Primary Key Uniqueness  | Exactly 270 rows   | PASSED   |
+--------------------+---------------------------------------------------+--------------------+----------+
| TC-DB-02           | Self-Referential Parent Scheme Cycle Detection    | 0 Circular Cycles  | PASSED   |
+--------------------+---------------------------------------------------+--------------------+----------+
| TC-DB-03           | Canonical State Array Validation                  | 0 Contradictions   | PASSED   |
+--------------------+---------------------------------------------------+--------------------+----------+
| TC-DB-04           | Required Documents JSON Schema Deserialization    | 0 String Literals  | PASSED   |
+--------------------+---------------------------------------------------+--------------------+----------+
| TC-DB-05           | Age Boundary Semantic Inversion (min_age > max)   | 0 Inverted Bounds  | PASSED   |
+--------------------+---------------------------------------------------+--------------------+----------+
| TC-VEC-01          | ChromaDB Collection Embedding Alignment           | 270 Multi-lang Vec | PASSED   |
+--------------------+---------------------------------------------------+--------------------+----------+
| TC-VEC-02          | Semantic Vector Search on Hindi Dialect Query     | Top-K Recall > 90% | PASSED   |
+--------------------+---------------------------------------------------+--------------------+----------+
```
*Table 4.1: Automated Test Verification Results for Completed Phases 1 and 2.*

### 4.2.2 End-to-End Case Study Walkthrough
To illustrate how the multi-tier system functions in practice, consider a realistic citizen interaction scenario:

- **Citizen Persona**: Smt. Ramvati Devi, a 42-year-old female resident of Barabanki district, Uttar Pradesh. She belongs to the Other Backward Classes (OBC), has an annual household income of ₹65,000, possesses 1.5 acres of agricultural land, and has no disability.
- **Stage 1 Execution**:
  - The voice interface systematically prompts Ramvati through the 9 baseline questions in clear spoken Hindi.
  - The citizen speaks her replies; IndicWhisper transcribes each utterance; the backend populates the in-memory Fact Profile:
    $$\{name: \text{'Ramvati'}, age: 42, gender: \text{'Female'}, state: \text{'Uttar Pradesh'}, income: 65000, category: \text{'OBC'}, occupation: \text{'Farmer'}, disability: False, need: \text{'खेती के लिए आर्थिक मदद और सोलर पंप'}\}$$
- **Stage 2 Execution**:
  - *Agent Iteration 1*: LangGraph agent evaluates profile need $\rightarrow$ calls `search_schemes("solar pump and farming support Uttar Pradesh", profile)`.
  - *MCP Server Response*: ChromaDB retrieves candidate schemes: *PM-KISAN* (ID 567), *PM KUSUM Solar Pump Scheme* (ID 112), and *UP Kisan Uday Yojana* (ID 204).
  - *Agent Iteration 2*: Agent passes candidates to `check_eligibility(profile, candidates)`.
  - *Deterministic Execution*:
    - *PM-KISAN*: Age $42 \ge 18$, Land $\le 2$ ha, State matches, Income compliant $\rightarrow$ **ELIGIBLE**.
    - *PM KUSUM*: Farmer status verified, Land verified, State matches $\rightarrow$ **ELIGIBLE**.
    - *Age-Ineligible Scheme (e.g. Youth Startup)*: Age $42 > 35$ $\rightarrow$ **INELIGIBLE (Failed criterion: Age exceeds statutory maximum of 35)**.
  - *Agent Iteration 3*: Agent identifies PM KUSUM requires land revenue record (*Khasra/Khatauni*). Calls `request_document("Khasra/Khatauni")`.
  - *Client Interface*: The mobile app prompts Ramvati in voice: *"कृपया अपने खेत की खतौनी की फोटो खींचे"*. Ramvati takes a photograph.
  - *OCR Processing*: OpenCV deskews the document; Tesseract extracts the land parcel record, confirming 1.5 acres in Barabanki.
  - *Resolution*: Total agent iterations = 3 ($\le 6$ bound). Agent synthesizes final Hindi response:
    *"रामवती जी, आप पीएम-किसान और पीएम-कुसुम सोलर पंप योजना के लिए पूरी तरह पात्र हैं। आपके पास खतौनी और आधार कार्ड मौजूद है। हमने आपके निकटतम सीएससी (कॉमन सर्विस सेंटर, हैदरगढ़) का पता भी आपके फोन पर भेज दिया है।"*

### 4.2.3 Next Steps Implementation Roadmap
Having conclusively stabilized and verified Phase 1 (Inception & Architecture) and Phase 2 (Corpus Engineering, PostgreSQL Schema, ChromaDB Multilingual Indexing, and Quality Audit at 0.990 score), the engineering roadmap for the immediate subsequent phases is defined as follows:

```
+---------------------------------------------------------------------------------------------------------+
|                                    NEXT STEPS IMPLEMENTATION ROADMAP                                    |
+---------------------------------------------------------------------------------------------------------+
| [CURRENT STATUS]                                                                                        |
| Phase 1: Architecture & Specifications ................................................ [COMPLETED]     |
| Phase 2: Corpus Scraping, Inconsistency Remediation & Vector Indexing ................. [COMPLETED]     |
+---------------------------------------------------------------------------------------------------------+
| [IMMEDIATE NEXT STEPS]                                                                                  |
| Phase 3: Deterministic Rules Engine (Week 6 - Week 7)                                                   |
|   - Implement `backend/app/services/rules_engine.py` using pure Python logic.                           |
|   - Formalize statutory predicate checkers for Age, Income, Gender, Caste, Disability, and State.       |
|   - Author 100% test coverage suite `backend/tests/test_rules_engine.py` evaluating edge cases.         |
|                                                                                                         |
| Phase 4: Voice Pipeline Server (Week 8 - Week 9)                                                        |
|   - Deploy AI4Bharat IndicWhisper / vasista22 Whisper ASR endpoint in `backend/app/services/stt.py`.     |
|   - Deploy AI4Bharat Indic-TTS endpoint in `backend/app/services/tts.py`.                               |
|   - Implement audio streaming and chunked multipart upload endpoints in FastAPI gateway.               |
|                                                                                                         |
| Phase 5: MCP Tool Server & LangGraph Orchestration (Week 10 - Week 11)                                  |
|   - Implement official Anthropic MCP server exposing the 4 statutory tools.                             |
|   - Construct LangGraph cyclic state machine with maximum 6-iteration bound and checkpointing.          |
|   - Connect local open-weight LLM (Llama-3 / Mistral via Ollama) as reasoning backend.                 |
|                                                                                                         |
| Phase 6: React Native Mobile Client Development (Week 12 - Week 13)                                     |
|   - Scaffold React Native CLI Android application in `/mobile`.                                         |
|   - Build Stage 1 scripted voice interview user interface with animated audio visualizer.             |
|   - Implement SQLite local cache for offline queueing of citizen recordings.                            |
|                                                                                                         |
| Phase 7: Document Capture & OCR Engine (Week 14 - Week 15)                                              |
|   - Build mobile camera document framing guide.                                                         |
|   - Implement OpenCV image deskewing and adaptive thresholding in `backend/app/services/ocr.py`.        |
|   - Integrate Devanagari Tesseract OCR extraction for Aadhaar, Ration Card, and Land Records.           |
|                                                                                                         |
| Phase 8: Empirical Evaluation & Final Dissertation (Week 16)                                            |
|   - Conduct field trials across benchmark personas measuring ASR WER, Latency, and Precision/Recall.    |
|   - Document statutory audit trail and write final Major Project Dissertation Report.                   |
+---------------------------------------------------------------------------------------------------------+
```
*Table 4.2: Structured Phase-Wise Engineering Roadmap for Project Completion.*

---
*End of Major Project Interim Report (Chapters 1 to 4).*
