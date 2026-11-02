# YojanaVaani — Antigravity Build Prompts
### Eight self-contained, copy-paste-ready prompts, one per build phase

## How to use this
Give these to Antigravity **one phase at a time**, in order. Don't move to the next prompt until you've verified the previous phase's acceptance criteria yourself — each prompt assumes the previous phases exist and works. Each prompt is self-contained (repeats the necessary project context) since you'll likely be starting a fresh Antigravity session per phase.

---

## Phase 1 — Project Foundation

```
PROJECT CONTEXT:
I am building "YojanaVaani" — a voice-first native Android app (React Native) that helps
Indian citizens, especially rural/low-literacy users, discover which government welfare
schemes they qualify for. The app works entirely by voice in Hindi: an assistant asks the
citizen a set of baseline questions (age, income, category, etc.), then an AI agent searches
a database of government schemes, asks scheme-specific follow-up questions if needed, verifies
facts via document photos (OCR), and speaks back a ranked list of schemes the citizen qualifies
for. This is a BTech major project with academic requirements: no TensorFlow, Keras, or Matlab
anywhere in the stack (institutional rule) — use PyTorch-based or classical ML tools instead
where any ML is needed later.

TASK FOR THIS PHASE:
Set up the complete project foundation and scaffolding only. Do not implement any AI logic yet.

1. Create a monorepo with this structure:
   /backend         -- Python FastAPI backend
   /mobile           -- React Native (TypeScript) mobile app
   /data-pipeline    -- Python scripts for scraping/indexing (to be filled in Phase 2)
   /docs             -- architecture notes
   /docker-compose.yml

2. Backend (/backend):
   - FastAPI application with a single working `/health` endpoint returning {"status": "ok"}.
   - PostgreSQL connection configured via SQLAlchemy, using environment variables (not
     hardcoded credentials) loaded through pydantic-settings or python-dotenv.
   - A clean modular structure: /backend/app/api, /backend/app/models, /backend/app/services,
     /backend/app/core (config, db session).
   - requirements.txt pinning FastAPI, SQLAlchemy, psycopg2-binary, pydantic-settings, uvicorn.
   - Dockerfile for the backend.

3. docker-compose.yml:
   - One service for the backend (built from its Dockerfile).
   - One service for PostgreSQL (official postgres image), with a named volume for persistence.
   - Backend depends_on postgres, with a healthcheck so backend waits for the DB to be ready.

4. Mobile app (/mobile):
   - Initialize a React Native project in TypeScript (use the React Native CLI, not Expo Go
     managed workflow, since we'll need native modules like camera and microphone access later).
   - A single placeholder screen showing "YojanaVaani" as a title and a placeholder microphone
     icon button (no functionality yet, just UI).
   - Basic React Navigation setup with one route, ready to add more screens later.

5. /docs/architecture.md:
   - Write a short architecture overview describing: React Native app -> FastAPI backend ->
     (future) STT/TTS/RAG/OCR services -> PostgreSQL. Note explicitly that all AI inference
     happens server-side; the mobile app is a lightweight client.

ACCEPTANCE CRITERIA (verify these before telling me you're done):
- `docker compose up` successfully starts both the backend and postgres containers.
- Visiting http://localhost:8000/health returns {"status": "ok"}.
- The React Native app builds and runs on an Android emulator, showing the placeholder screen.
- Project structure matches what's described above.

Do not add any speech, ML, or OCR code in this phase — foundation and scaffolding only.
```

---

## Phase 2 — Scheme Database

```
PROJECT CONTEXT:
This is Phase 2 of "YojanaVaani," a voice-first Android app that helps Indian citizens discover
government schemes they qualify for. Phase 1 already set up the project foundation: a FastAPI
backend in /backend, a React Native app in /mobile, and PostgreSQL running via docker-compose.
Do not modify the Phase 1 scaffolding except to add new tables/models.

TASK FOR THIS PHASE:
Build the scheme database: scrape, structure, and index government scheme data so it can be
searched later by an AI agent. This is a data pipeline task, not a mobile app task.

1. Scraping script (/data-pipeline/scrape_schemes.py):
   - Scrape scheme listings and detail pages from https://www.myscheme.gov.in/
   - To keep scope defensible for a semester project, limit v1 to schemes from 4-5 categories
     most relevant to our target users: Agriculture, Education, Women & Child, Health, and
     Housing. Do not attempt to scrape all 2,300+ schemes.
   - Respect the site's robots.txt, add a polite delay (1-2 seconds) between requests, and
     handle failures gracefully — if one scheme page fails to parse, log it and continue,
     don't crash the whole run.
   - For each scheme, extract and structure these fields:
     - name, category, ministry_or_department
     - eligibility_criteria as a structured sub-object where possible: min_age, max_age,
       income_ceiling, applicable_states (list), social_category (list, e.g. SC/ST/OBC/General),
       gender, occupation, disability_status, other_conditions_text (free text for anything
       that doesn't fit the structured fields — do not lose information by forcing everything
       into structured fields)
     - benefits (free text)
     - required_documents (list of strings)
     - application_process (free text)
     - source_url, last_scraped_at (timestamp)

2. Database model (/backend/app/models/scheme.py):
   - A SQLAlchemy model `Scheme` matching the fields above, with eligibility_criteria stored
     as JSONB (PostgreSQL JSON column) since it's semi-structured.
   - A migration (using Alembic) to create this table.

3. Loader script (/data-pipeline/load_schemes.py):
   - Reads the scraped data and inserts/upserts it into the `schemes` table (upsert on
     source_url so re-running doesn't create duplicates).

4. Embedding and indexing script (/data-pipeline/build_index.py):
   - Use a multilingual sentence-embedding model (sentence-transformers library, model
     "paraphrase-multilingual-mpnet-base-v2" or similar multilingual model) to embed a
     concatenated text representation of each scheme (name + category + eligibility text +
     benefits).
   - Store the embeddings in Chroma (persisted locally in a Docker volume), with each vector
     linked back to the scheme's database ID.
   - This script should be safely re-runnable to rebuild the index after a re-scrape.

5. Manual retrieval test script (/data-pipeline/test_retrieval.py):
   - A simple CLI script: takes a typed text query as input, embeds it, searches Chroma,
     and prints the top-5 matching scheme names with their similarity scores.
   - This is for YOU to manually sanity-check retrieval quality before any voice integration
     happens in later phases — no automated test needed, just a usable CLI tool.

ACCEPTANCE CRITERIA (verify these before telling me you're done):
- Running the scrape -> load -> build_index pipeline populates the `schemes` table with at
  least 100-150 real schemes across the 4-5 target categories.
- test_retrieval.py, given queries like "scheme for daughter's education" or "farmer loan
  scheme," returns sensible, actually-relevant scheme names in the top 5.
- The pipeline can be re-run without creating duplicate entries.

Do not implement any speech-to-text, agent, or mobile UI code in this phase.
```

---

## Phase 3 — Assistant-Led Interview Script

```
PROJECT CONTEXT:
This is Phase 3 of "YojanaVaani." Phases 1-2 built the project foundation and a scheme
database (PostgreSQL table `schemes` + Chroma vector index, searchable via
/data-pipeline/test_retrieval.py). This phase does NOT touch speech or the mobile app —
it builds the conversation logic in plain text first, so it can be tested and verified
before voice is layered on top in Phase 4.

DESIGN DECISION TO FOLLOW EXACTLY:
The conversation has two stages. Stage one is a FIXED baseline interview — the same questions,
in the same order, for every citizen, covering fields almost every scheme's eligibility depends
on. Stage two (built in Phase 5) is an AGENTIC follow-up loop for scheme-specific gaps. This
phase only builds stage one. Do not make the baseline interview questions dynamic or
agent-decided — they must be a fixed, predictable script.

TASK FOR THIS PHASE:
1. Conversation state model (/backend/app/models/conversation.py):
   A Pydantic model (or SQLAlchemy model + Pydantic schema) representing conversation state:
   - conversation_id
   - citizen_profile: { name, age, gender, state, district, approx_income_bracket,
     social_category, occupation, disability_status }
   - stated_need: free text (what the citizen says they're looking for)
   - baseline_complete: bool
   - collected_documents: list (empty for now, used in Phase 6)
   - conversation_history: list of {speaker, text, timestamp}
   - candidate_schemes: list (empty for now, used in Phase 5)
   - missing_facts: list (empty for now, used in Phase 5)
   - status: enum (e.g. "baseline_interview", "scheme_matching", "awaiting_document",
     "results_ready", "escalated")

2. Baseline question script (/backend/app/services/baseline_interview.py):
   Write the fixed sequence of baseline questions in Hindi (Devanagari script), each as a
   short, simple, spoken-language-appropriate sentence (not formal written Hindi) --
   for example, for age: "aapki umar kya hai?" written in Devanagari. Cover, in this order:
   name, age, gender, state/district, approximate income (offer income brackets rather than
   an exact number, since exact income is hard to state verbally -- e.g. "2 lakh se kam,
   2 se 5 lakh, 5 lakh se zyada"), social category, occupation, disability status, and finally
   an open-ended question: "aap kis tarah ki sarkari sahayata dhoondh rahe hain?" (what kind
   of government help are you looking for).

3. ConversationManager class (/backend/app/services/conversation_manager.py):
   - Tracks which baseline questions have been asked and answered for a given conversation_id.
   - Method `get_next_question(conversation_id) -> str | None`: returns the next unanswered
     baseline question in Hindi, or None if baseline is complete.
   - Method `record_answer(conversation_id, question_field, answer_text)`: stores the answer
     into citizen_profile, handling simple parsing (e.g. mapping spoken income-bracket answers
     to the income_bracket enum).
   - When all baseline questions are answered, set status to "scheme_matching" and
     baseline_complete to True.

4. Text-only test harness (/backend/scripts/test_interview_cli.py):
   A command-line script that simulates a full conversation: prints each baseline question,
   accepts typed input (standing in for what would later be transcribed speech), and shows
   the citizen_profile being filled in turn by turn, ending with a printed confirmation that
   baseline is complete and status has moved to "scheme_matching".

ACCEPTANCE CRITERIA (verify these before telling me you're done):
- Running test_interview_cli.py lets you walk through the entire baseline interview via
  typed input.
- citizen_profile is correctly populated field by field.
- The manager correctly reports baseline_complete=True and status="scheme_matching" after
  the last question.

Do not implement speech-to-text, text-to-speech, the AI agent, or OCR in this phase.
```

---

## Phase 4 — Hindi Speech-to-Text and Text-to-Speech

```
PROJECT CONTEXT:
This is Phase 4 of "YojanaVaani." Phases 1-3 built the backend foundation, the scheme
database, and a text-based conversation manager (ConversationManager, tested via a CLI
harness with typed input). This phase adds real Hindi speech input/output as standalone,
independently testable backend services -- it does NOT yet connect them to the
ConversationManager or the mobile app. That wiring happens in Phase 7.

TASK FOR THIS PHASE:
1. ASR (speech-to-text) service (/backend/app/services/asr_service.py):
   - Define an abstract `ASRProvider` interface with a method
     `transcribe(audio_bytes, language_code) -> TranscriptionResult` where
     TranscriptionResult has {text, confidence, language_code}.
     This abstraction exists because the official AI4Bharat IndicWhisper model is currently
     gated on Hugging Face -- build this so a provider can be swapped later without touching
     calling code.
   - Implement `VasistaWhisperProvider` using the vasista22 Whisper-large-v2 Hindi fine-tune
     from Hugging Face (openly licensed, no gating) as the default provider for now.
   - Load the model once at startup (not per-request) for reasonable latency.

2. TTS (text-to-speech) service (/backend/app/services/tts_service.py):
   - A `TTSProvider` interface with method `synthesize(text, language_code) -> audio_bytes`.
   - Implement using AI4Bharat's Indic-TTS or IndicF5 (whichever has clearer setup
     documentation available -- use your judgment, note which one you picked and why in a
     code comment).

3. API endpoints (/backend/app/api/speech.py):
   - POST /stt: accepts an uploaded audio file + language_code, returns transcribed text +
     confidence as JSON.
   - POST /tts: accepts text + language_code, returns synthesized audio (as a file response
     or base64-encoded audio in JSON -- pick whichever is simpler to test, note your choice).
   - If STT confidence is below a threshold (e.g. 0.6), include a `low_confidence: true` flag
     in the response so calling code can later prompt the user to repeat themselves.

4. Test harness (/backend/scripts/test_speech.py):
   - Script that sends a set of pre-recorded Hindi audio sample files (you can generate these
     yourself using any Hindi TTS tool, or ask me to record real samples if you need them --
     note in your output which approach you used) through /stt and prints transcriptions
     alongside expected text, computing word error rate.
   - Script that sends a set of Hindi text phrases through /tts and saves the resulting audio
     files locally so they can be manually listened to and checked for intelligibility.

ACCEPTANCE CRITERIA (verify these before telling me you're done):
- POST /stt, given a Hindi audio file, returns a reasonable transcription with a confidence
  score.
- POST /tts, given Hindi text, returns audio that is audibly intelligible Hindi speech when
  played back.
- The WER test script runs and reports a word error rate number (don't worry about hitting
  a specific target yet -- just get the measurement pipeline working; we'll use this number
  in the evaluation chapter later).

Do not connect this to ConversationManager or the mobile app yet -- these are standalone,
independently testable endpoints only.
```

---

## Phase 5 — RAG and Agentic Reasoning Layer

```
PROJECT CONTEXT:
This is Phase 5 of "YojanaVaani," the most architecturally important phase. Phases 1-4 built:
a scheme database (PostgreSQL + Chroma vector index, Phase 2), a ConversationManager that
completes a fixed baseline interview and produces a citizen_profile (Phase 3), and standalone
Hindi STT/TTS services (Phase 4). This phase builds the agentic reasoning layer that takes
over once the baseline interview is complete.

CRITICAL DESIGN RULE -- FOLLOW THIS EXACTLY, IT IS NOT OPTIONAL:
The system uses an LLM-driven agent that decides, at each turn, which tool to call next.
BUT the agent must NEVER be the thing that decides whether a citizen is eligible for a
scheme -- that decision must always come from a separate, deterministic, rule-based function
(built as a stub in this phase, fully implemented in Phase 6), which the agent calls as a
tool. The agent's job is to decide WHEN to call that tool and WHAT other information to
gather first (via search or follow-up questions) -- never to reason its way to an eligibility
verdict on its own. If you find yourself writing prompt instructions that ask the LLM to
directly state whether someone qualifies, stop -- that logic belongs in the deterministic
tool, not the agent's own reasoning.

TASK FOR THIS PHASE:
1. Set up an open-weight LLM locally via Ollama (use a small-to-medium model appropriate for
   a development machine, e.g. a Llama or Mistral variant -- pick one that's practical to run
   locally and note your choice).

2. Implement four tools using the MCP Python SDK (https://github.com/modelcontextprotocol/python-sdk),
   exposed via an MCP server (/backend/app/mcp/tools.py):
   - `search_schemes(query: str, profile: dict) -> list[SchemeCandidate]`: embeds the query
     (combining the citizen's stated_need and relevant profile fields), searches the Chroma
     index built in Phase 2, and returns the top-k candidate schemes with their full
     eligibility_criteria.
   - `request_document(document_type: str) -> str`: for THIS phase, implement as a stub that
     returns a placeholder message (real OCR wiring happens in Phase 6) -- but define the
     real interface now so Phase 6 slots in cleanly.
   - `check_eligibility(profile: dict, candidate_schemes: list) -> list[EligibilityVerdict]`:
     for THIS phase, implement as a stub returning a placeholder verdict for each candidate
     (real deterministic logic happens in Phase 6) -- again, define the real interface now.
   - `escalate_to_csc(reason: str) -> dict`: returns placeholder nearest-Common-Service-Centre
     info (a hardcoded example location is fine for now).

3. Agent orchestration (/backend/app/services/agent.py):
   - Use LangGraph (https://github.com/langchain-ai/langgraph) to build a tool-calling loop:
     the agent receives the citizen_profile and stated_need, and the four MCP tools, with a
     system prompt instructing it to: (a) reason only from information actually retrieved via
     search_schemes, never invent scheme details, (b) identify what additional facts are
     needed to reach a confident answer and either ask a clarifying follow-up question (return
     this as a distinct response type, not a tool call) or call request_document, (c) call
     check_eligibility once it believes it has enough information, (d) call escalate_to_csc if
     it cannot make progress after a few turns.
   - Hard-limit the agent to a maximum of 6 tool-call iterations per conversational turn to
     prevent runaway loops.
   - Wire this so that once ConversationManager's status becomes "scheme_matching" (from
     Phase 3), control passes to this agent with the citizen_profile and stated_need as
     input.

4. Text-only test harness (/backend/scripts/test_agent_cli.py):
   - Build 10 hand-written test scenarios (citizen_profile + stated_need combinations covering
     different categories -- e.g. a farmer asking about irrigation support, a mother asking
     about a daughter's education scheme) and run each through the agent, printing out: which
     tools were called, in what order, what candidate schemes were found, and what follow-up
     question (if any) the agent asked.

ACCEPTANCE CRITERIA (verify these before telling me you're done):
- For all 10 test scenarios, the agent calls search_schemes at least once and returns
  candidate schemes that are actually topically relevant to the stated need.
- When a scheme's eligibility_criteria includes a field not present in citizen_profile, the
  agent identifies this as a missing fact and asks about it or requests a document, rather
  than silently ignoring it or making an assumption.
- The agent never states an eligibility verdict directly in its own generated text -- it always
  routes through the (stub) check_eligibility tool.
- No test scenario exceeds the 6-iteration tool-call limit without reaching a conclusion or
  escalating.

Do not implement the real OCR or real eligibility-matching logic in this phase -- those stay
as stubs, to be filled in during Phase 6.
```

---

## Phase 6 — Eligibility Matching Engine and OCR Document Verification

```
PROJECT CONTEXT:
This is Phase 6 of "YojanaVaani." Phase 5 built the agentic reasoning layer with two tools
left as stubs: check_eligibility and request_document. This phase replaces both stubs with
real implementations. Do not modify the agent orchestration logic from Phase 5 -- only
replace the internal implementation of these two tools, keeping their function signatures
identical so nothing else needs to change.

TASK FOR THIS PHASE:
1. Deterministic eligibility engine (/backend/app/services/eligibility_engine.py):
   - This MUST be plain Python logic -- no LLM calls anywhere in this function. This is a
     deliberate, non-negotiable design choice: the actual eligibility decision must be
     auditable and rule-based, not a black-box language model guess.
   - Function `evaluate_scheme(profile: dict, scheme: Scheme) -> EligibilityVerdict` that
     checks each field in the scheme's eligibility_criteria against the citizen_profile:
     age within [min_age, max_age], income within income_ceiling, social_category match,
     applicable_states match, gender match, occupation match, disability_status match, and
     free-text other_conditions (flag these as "needs manual review" rather than trying to
     parse free text with rules -- be honest about this limitation in a code comment).
   - Return one of three verdicts per scheme: QUALIFIES, NEEDS_MORE_INFO (with which specific
     field is missing), or DOES_NOT_QUALIFY (with the specific disqualifying reason, e.g.
     "income exceeds the ceiling for this scheme").
   - Wire this into the real `check_eligibility` MCP tool, replacing the Phase 5 stub, ranking
     candidate schemes by verdict (QUALIFIES first) and returning the full ranked, justified
     list.

2. OCR document verification (/backend/app/services/ocr_service.py):
   - Use Tesseract (via pytesseract) with both Hindi and English language packs installed.
   - Image pre-processing pipeline using OpenCV before OCR: deskew, contrast normalization,
     and cropping guidance.
   - Field extraction: given a document_type (e.g. "ration_card", "income_certificate"),
     apply a targeted extraction approach (regex or positional heuristics appropriate to
     common Indian document layouts) to pull out the specific fields relevant to eligibility
     checking (name, age/DOB, address, income figure, category), each with a confidence score.
   - Wire this into the real `request_document` MCP tool, replacing the Phase 5 stub: it should
     trigger a request for a photo (the actual photo capture UI comes in Phase 7 -- for now,
     accept an uploaded image file directly via an API endpoint for testing), run it through
     OCR, and return the extracted structured fields.
   - Add a `/documents/confirm` endpoint: given extracted fields, returns them in a format
     ready for a yes/no confirmation step (the actual confirmation UI comes in Phase 7).

3. Mock test document generation:
   - Create or generate 10-15 mock document images (ration card / income certificate style,
     NOT real people's actual identity documents -- create synthetic examples with placeholder
     names and data) to use as a test set for the OCR pipeline. Note clearly in your output
     that these are synthetic test documents, not real identity documents.

4. Test harness (/backend/scripts/test_eligibility_and_ocr.py):
   - A test matrix: for a set of hand-built citizen_profile x scheme combinations with known
     correct answers, run evaluate_scheme and check whether the verdict matches expectations.
   - Run the mock document set through the OCR pipeline and report per-field extraction
     accuracy.

ACCEPTANCE CRITERIA (verify these before telling me you're done):
- The eligibility test matrix produces correct QUALIFIES / NEEDS_MORE_INFO / DOES_NOT_QUALIFY
  verdicts matching your hand-verified expected answers.
- OCR correctly extracts at least 70% of fields on the mock document set, with confidence
  scores exposed for every extraction (including the ones that failed) so this can be reported
  honestly in the evaluation chapter later.
- The full agent flow (from Phase 5) now runs end-to-end with real eligibility and OCR logic
  instead of stubs, when tested via the Phase 5 CLI harness.
```

---

## Phase 7 — React Native Mobile App

```
PROJECT CONTEXT:
This is Phase 7 of "YojanaVaani." Phases 1-6 built and independently tested the entire
backend: scheme database, conversation manager, Hindi STT/TTS, the agentic reasoning layer,
and real eligibility/OCR logic. All of this is currently only testable via CLI harnesses and
curl/Postman. This phase builds the actual mobile app UI and wires it to the already-working
backend -- this phase should involve very little new backend logic, mostly UI and API
integration, because the hard logic was already built and tested in earlier phases.

TASK FOR THIS PHASE:
1. First, add ONE new backend endpoint that ties everything together for the mobile app to
   call (/backend/app/api/conversation.py):
   - POST /conversation/start: creates a new conversation_id, returns the first baseline
     question as both text and synthesized audio (using the Phase 4 TTS service).
   - POST /conversation/{id}/respond: accepts an uploaded audio file (the citizen's spoken
     answer), runs it through STT (Phase 4), records the answer via ConversationManager
     (Phase 3), and returns the NEXT action for the app to take -- one of:
     {type: "ask_question", text, audio_url}, {type: "request_document", document_type},
     {type: "present_results", schemes: [...], audio_url}, or
     {type: "escalate", csc_info, audio_url}.
   - POST /conversation/{id}/document: accepts an uploaded document photo, runs it through
     OCR (Phase 6), returns extracted fields for confirmation.
   - POST /conversation/{id}/confirm_document: accepts yes/no confirmation of extracted
     fields, updates the conversation state, and returns the next action (same format as
     /respond).
   This single conversational endpoint pattern means the mobile app only needs to manage a
   simple "send audio or confirmation, receive next action" loop -- it should not need to
   know anything about the internal agent/tool-calling logic.

2. Mobile app screens (in /mobile, building on the Phase 1 scaffolding):
   - Onboarding screen: explains in simple Hindi what the app does and requests microphone
     and camera permissions with a plain-language explanation of why each is needed (proper
     Android runtime permission handling, not just a manifest declaration).
   - Main conversation screen: opens directly into the assistant speaking its first question
     (auto-plays the audio from /conversation/start) -- not a blank screen waiting for the
     user to know what to say. Large mic button to record a response. Visual indicator while
     the assistant is "speaking" vs "listening." Optional: a simple visual transcript of the
     conversation so far, for citizens who can read some text (secondary channel, not primary).
   - Document capture screen: opens the camera when the backend requests a document, shows a
     review/retake option before submitting, then shows extracted fields read back for a
     yes/no voice confirmation.
   - Results screen: displays the ranked scheme list visually AND plays the spoken summary
     automatically.
   - Escalation screen: shows nearest Common Service Centre info when the backend returns an
     escalate action.

3. Offline/connectivity handling:
   - Use a local SQLite store (react-native-sqlite-storage or similar) to queue a recorded
     audio response if the network request to /conversation/{id}/respond fails, with a clear
     "waiting to send" UI state, and automatic retry when connectivity returns. Do not lose
     the citizen's recorded answer if the network drops.

ACCEPTANCE CRITERIA (verify these before telling me you're done):
- On an Android emulator (or physical device), a full conversation can be completed end to
  end: onboarding -> baseline interview (spoken questions, spoken answers) -> agent follow-up
  questions if triggered -> document capture and confirmation if triggered -> ranked results
  shown and spoken aloud.
- If the network is disabled mid-conversation, a recorded response is queued locally and
  successfully sent once the network is restored, without losing the citizen's answer.
- Microphone and camera permission requests show a clear Hindi explanation before the OS
  permission dialog appears.
```

---

## Phase 8 — Testing, Evaluation, and Polish

```
PROJECT CONTEXT:
This is Phase 8, the final phase of "YojanaVaani." Phases 1-7 built a fully working
end-to-end system: scheme database, Hindi STT/TTS, an agentic RAG reasoning layer with
MCP-exposed tools, a deterministic eligibility engine, OCR document verification, and a
React Native mobile app. This phase does not add new features -- it builds the evaluation
harness needed to turn this from "a working demo" into a properly evaluated academic project
with defensible, honestly-reported results.

TASK FOR THIS PHASE:
1. ASR accuracy evaluation (/backend/evaluation/eval_asr.py):
   - Using the recorded Hindi evaluation query set from Phase 4, compute and report word
     error rate, broken down per question type (baseline questions vs. open-ended stated_need
     queries, since these likely differ in difficulty).

2. Retrieval accuracy evaluation (/backend/evaluation/eval_retrieval.py):
   - Build a set of at least 30 question-answer pairs (query -> the scheme(s) that should be
     the correct top result) manually constructed from the actual scraped scheme data.
   - Compute top-k retrieval accuracy (what fraction of queries return the correct scheme in
     the top 3 or top 5 results).

3. Hallucination rate evaluation (/backend/evaluation/eval_hallucination.py):
   - Build a harness that, for a sample of agent-generated answers, presents the answer
     alongside the actual retrieved scheme text side by side, for a human rater (you) to mark
     whether the answer is fully supported by the retrieved text or contains an unsupported
     claim. Report the resulting hallucination rate as a percentage.

4. OCR accuracy evaluation (/backend/evaluation/eval_ocr.py):
   - Using the Phase 6 mock document test set, report per-field extraction accuracy, and
     separately test against a second, deliberately lower-quality set of document photos
     (angled, poorly lit, taken with a basic phone camera) to honestly characterize the real-
     world accuracy gap versus clean test images.

5. Agent tool-call correctness evaluation (/backend/evaluation/eval_agent_trajectory.py):
   - Build at least 10 multi-turn conversation scenarios (citizen volunteers information
     early, asks an off-order follow-up, has a document ready unprompted, etc.) with an
     expected correct or acceptable sequence of tool calls for each, and report what fraction
     of scenarios the agent handles sensibly.

6. End-to-end task success rate (/backend/evaluation/eval_e2e.py):
   - Using a combined evaluation set spanning multiple scheme categories, report what fraction
     of full conversations (start to a correct, complete spoken result) succeed without
     needing escalation.

7. Results summary (/backend/evaluation/generate_report.py):
   - A single script that runs all the above and outputs a summary (as a markdown file and/or
     simple charts, e.g. using matplotlib) with all the key numbers formatted and ready to
     drop into a final project report.

8. Usability check:
   - Write a short, structured feedback form (a markdown or text template is fine) for running
     an informal usability session with a handful of volunteers unfamiliar with the app,
     covering: could they complete a realistic query without help, did the assistant-led
     interview feel natural or repetitive, was the spoken output clear and understandable.

ACCEPTANCE CRITERIA (verify these before telling me you're done):
- generate_report.py runs successfully end to end and produces a single summary document
  containing all six categories of evaluation results above.
- Every metric is reported honestly, including any that come out lower than hoped -- do not
  filter out or hide weak results; a project report that only shows best-case numbers is
  weaker, not stronger, for an academic evaluation.
```
