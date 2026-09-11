# YojanaVaani: Voice-First Government Scheme Navigator

## Full Specification & Academic Foundations

Voice-First Government Scheme Navigator

Complete Project Specification


## 1. Overview

Millions of Indian citizens are entitled to government welfare schemes they never claim, simply because they cannot read the eligibility rules, do not know the schemes exist, or cannot navigate a text-heavy web portal. This project builds a voice-first native mobile application — installed from the Play Store or side-loaded as an APK, not a website opened in a browser — that lets a citizen speak a question in their own language — "Am I eligible for a housing scheme?" — and receive a spoken, personalized answer, verified against their own documents, without needing to read a single word.

A native app is the right call here, not a website, for reasons specific to this user base: it needs microphone and camera access with proper Android runtime permission handling, it needs to work with degraded connectivity (a website tab can be lost on a flaky connection; a native app can queue and retry), and the target user is someone who navigates their phone primarily through app icons, not a browser and typed URLs.

The system is built by integrating four independent, pre-existing open-source AI components into one working pipeline: speech-to-text, retrieval-grounded reasoning over scheme rules, document verification via OCR, and speech synthesis. None of these components solve the citizen's actual problem alone — the integration layer connecting them is the project's original contribution.


## 2. Literature Survey


### 2.1 The motivating research

This exact use case is not a hypothetical — it is explicitly named in the peer-reviewed research behind one of this project's core components. The Vistaar paper (Bhogale, Sundaresan, Raman, Javed, Khapra, and Kumar, 2023), which introduced the IndicWhisper speech recognition models, states its core motivation as follows: an Indian villager could interact with an LLM-based system to learn about rights and entitlements on existing government schemes, and to make such use-cases accessible to a large population, it is essential to make them voice-enabled. The same paper grounds why this matters at national scale: India has 60 languages with over a million speakers each, and over 300 million print-illiterate people, making accurate speech recognition a matter of significant societal impact, not just convenience.

Links: Paper (arXiv) — https://arxiv.org/abs/2305.15386 · Full text (ar5iv) — https://ar5iv.labs.arxiv.org/html/2305.15386 · Interspeech 2023 version (PDF) — https://www.isca-archive.org/interspeech_2023/bhogale23_interspeech.pdf


### 2.2 The scale of the awareness and access gap

Independent research confirms the underlying problem is real and large. National Sample Survey Office data (78th round, 2020-21) found that computer literacy among persons aged 15 and above stood at only 24.7% nationally, with a sharp rural-urban split — 18.1% in rural regions against 39.6% in urban regions. A 2025 study examining Digital India's impact on rural development surveyed rural populations and ranked the barriers to digital scheme access: lack of digital literacy ranked first, poor internet connectivity second, the cost of smartphones and data third, and lack of awareness about government schemes specifically fourth — with respondents themselves recommending more awareness campaigns and more Common Service Centres as the two most-needed interventions.

A quasi-experimental study conducted in rural Jharkhand (2017-2020) offers direct evidence that closing this gap changes outcomes: after a digital literacy training program for adolescent girls, the intervention group showed a significantly higher rate of awareness of government schemes compared to the untrained comparison group, alongside improvements in continued schooling and perceived safety. This confirms that the barrier is genuinely addressable — but a training program is slow, resource-intensive, and cannot scale to hundreds of millions of people. A voice-first, no-reading-required system is a fundamentally different, more scalable approach to the same problem.

Links: NSSO 78th round statistics, as cited in "Digital literacy and E-government in India" — https://www.humanitiesjournal.net/archives/2026/vol8issue1/PartA/8-1-8-950.pdf · "Examining the Role of Digital India in Rural Development" (2025) — https://www.researchgate.net/publication/395530377_Examining_the_Role_of_Digital_India_in_Rural_Development · Digital literacy training programme study, PLOS Digital Health (2025) — https://journals.plos.org/digitalhealth/article?id=10.1371%2Fjournal.pdig.0000617 (mirror: https://pmc.ncbi.nlm.nih.gov/articles/PMC11984724/) · "Digital Literacy In India: Achievements And Challenges" (2025) — https://www.ijcrt.org/papers/IJCRT25A4851.pdf · "The digital revolution in India: bridging the gap in rural technology adoption" — https://innovation-entrepreneurship.springeropen.com/articles/10.1186/s13731-024-00380-w · Digital literacy programs and the urban-rural divide — https://industrywired.com/digital-payments/digital-literacy-programs-bridging-indias-urban-rural-divide-8605557


### 2.3 What already exists, and its specific limitation

The Government of India has already built the natural starting point for this problem: myScheme, a national platform (launched July 2022, operated by the National e-Governance Division under MeitY) that consolidates over 2,300 schemes across 15 categories from central and state governments into one searchable platform. Its "Personalised Search" and "Check Eligibility Questionnaire" features let a citizen enter demographic details — age, gender, income, social category, state, disability status — and receive a filtered list of schemes they may qualify for.

This is exactly the gap this project addresses. myScheme's own documentation describes the discovery process as a three-step flow: the user enters basic details, the platform displays relevant schemes, and the user navigates to the respective application URL to apply. Every step of that flow assumes the citizen can read a form, type demographic details, and read the resulting scheme list. There is no voice interface, and no mechanism to auto-extract a citizen's details from a photograph of their existing documents — a citizen still has to know their own eligibility-relevant facts and enter them manually. For the print-illiterate and low-digital-literacy population the research above identifies as the primary barrier group, myScheme's existing design does not solve the access problem it was built for.

Links: myScheme (main site, and the scraping source for the scheme corpus) — https://www.myscheme.gov.in/ · myScheme About — https://www.myscheme.gov.in/about · myScheme FAQs (documents the existing "Personalised Search"/"Check Eligibility Questionnaire" flow this project extends) — https://www.myscheme.gov.in/faqs · myScheme — National e-Governance Division project page — https://negd.gov.in/myscheme/ · myScheme — Digital India Corporation page — https://dic.gov.in/my-scheme/ · myScheme — Digital India initiative page — https://www.digitalindia.gov.in/initiative/myscheme/ · myScheme Android app — https://play.google.com/store/apps/details?id=in.gov.negd.myscheme&hl=en


### 2.4 The AI components this project draws on

Speech recognition for Indian languages: AI4Bharat (a research lab at IIT Madras, developed with support from the Digital India Bhashini mission, MeitY, and philanthropic partners) fine-tuned OpenAI's Whisper model on 10.7 thousand hours of speech across 12 Indian languages to produce IndicWhisper, evaluated against their own Vistaar benchmark of 59 language-domain combinations. IndicWhisper achieved the lowest word error rate in 39 of the 59 benchmarks tested, with an average WER reduction of 4.1 points over other publicly available and commercial ASR systems evaluated in the same study.

Retrieval-augmented generation (RAG): a well-established technique for grounding large language model outputs in a specific, verifiable document set rather than the model's general training data, reducing hallucination risk — critical for a system giving eligibility information that affects real financial decisions.

Optical character recognition for structured documents: Tesseract, a mature, widely used open-source OCR engine, capable of extracting text fields from photographed identity and income documents.

Indian-language speech synthesis: AI4Bharat's Indic-TTS project, producing natural-sounding synthetic speech across Indian languages, allowing the system to close the loop by speaking its answer back rather than displaying text the citizen may not be able to read.


### 2.5 Literature gap this project fills

No existing published system or deployed platform combines all four of the above into a single voice-to-eligibility-to-application pipeline. The research introducing IndicWhisper names the use case as a future possibility, not a built system. myScheme solves scheme discovery but requires literacy and manual data entry. This project's contribution is the integration: a working system where a citizen who cannot read or type still receives an accurate, document-verified, spoken answer to "what am I entitled to."


## 3. Complete Application Flow

CITIZEN SPEAKS QUERY

(Hindi / regional language)

|

v

+-------------------------+

| 1. VOICE QUERY CAPTURE  |   Single-tap mic button, no menus

+-------------------------+

|

v

+-------------------------+

| 2. SPEECH-TO-TEXT       |   IndicWhisper (or vasista22 fallback)

|    (IndicWhisper)       |   -> transcribed text + confidence score

+-------------------------+

|

v

+----------------------------------+

| 3. RAG ELIGIBILITY REASONING     |   Text embedded -> FAISS/Chroma

|    (LangChain + vector DB + LLM) |   vector search over scheme corpus

+----------------------------------+   -> candidate schemes + missing facts

|

v

+-------------------------+

| 4. DOCUMENT VERIFICATION|   Citizen photographs ID/income proof

|    (Tesseract OCR)      |   -> extracted structured fields

+-------------------------+

|

v

+-------------------------------+

| 5. ELIGIBILITY MATCHING       |   Deterministic rules engine cross-checks

|    (custom rules engine)      |   extracted facts against scheme criteria

+-------------------------------+   -> ranked, justified eligibility list

|

v

+-------------------------+

| 6. SPOKEN RESPONSE      |   Indic-TTS reads back results

|    (Indic-TTS)          |   in the citizen's own language

+-------------------------+

|

+----------------------------+

|                            |

v                            v

+-------------------+      +--------------------------+

| 7. FOLLOW-UP LOOP  |      | 8. HUMAN ESCALATION      |

|    (multi-turn,    |      |    (if confidence low /  |

|    context kept)   |      |    unresolved query)     |

+-------------------+      | -> nearest Common Service |

|                  |    Centre / helpline      |

v                  +--------------------------+

back to stage 2/3

for the next question

Stage 1 — Voice query capture

The citizen opens the app and taps a single large microphone button (no menus, no text fields visible by default) and speaks their question naturally in their own language — for example, "Mujhe beti ki padhai ke liye koi sarkari yojana chahiye" (I need a government scheme for my daughter's education).

Stage 2 — Speech-to-text transcription

The captured audio is passed to IndicWhisper, which transcribes it into text in the same language, along with a confidence score. If confidence is low (noisy environment, heavy dialectal variation), the app asks the citizen to repeat the query rather than silently guessing.

Stage 3 — RAG-based eligibility reasoning

The transcribed text query is embedded and passed into a retrieval-augmented generation pipeline built on LangChain. The system searches a pre-indexed vector database containing structured scheme data (name, category, eligibility criteria, benefits, required documents, application process) scraped from myScheme, and retrieves the most relevant candidate schemes. An open-weight LLM then reasons over the retrieved scheme text — not its own general knowledge — to identify which schemes are plausibly relevant to the stated need, and what specific eligibility facts (age, income, category, land ownership, etc.) still need to be confirmed before a final answer can be given.

Stage 4 — Document verification (OCR)

Rather than asking the citizen to state their age, income bracket, or category verbally (error-prone and burdensome), the app asks them to photograph one or two documents they likely already have on hand — a ration card, an income certificate, an Aadhaar card. Tesseract OCR extracts the relevant structured fields (name, age/DOB, address, income bracket, category) from the image.

Stage 5 — Eligibility matching and ranking

The facts extracted from the citizen's documents are cross-referenced against the eligibility rules of every scheme retrieved in Stage 3. This produces a ranked list: schemes the citizen clearly qualifies for, schemes needing one more piece of information, and schemes they don't currently qualify for (with the specific disqualifying reason, since that transparency builds trust and is often useful information in itself — e.g., "you need one more year of residency in this state").

Stage 6 — Spoken response

The ranked result, in plain language, is converted to speech using Indic-TTS and played back to the citizen in the same language they spoke in: which schemes they qualify for, what benefit each provides, and the concrete next step (which office to visit, which documents to bring, or a link if they have someone who can help them apply online).

Stage 7 — Human escalation (fallback path)

If the query is ambiguous, the retrieved schemes are inconclusive, or the citizen explicitly asks for more help, the app provides the location and contact details of the nearest Common Service Centre — the existing, government-run, in-person channel already used for exactly this kind of assistance. The app is designed to extend the reach of the existing system, not replace the human fallback it depends on.

Stage 8 — Follow-up conversation (multi-turn)

The citizen can ask follow-up questions by voice — "What documents do I need to bring?" or "What if I don't have an income certificate?" — and the system maintains conversational context so it doesn't restart the eligibility search from scratch each time.


## 4. Detailed Explanation of Each Integrated Component


### 4.1 IndicWhisper (speech-to-text)

What it is: A family of automatic speech recognition models produced by AI4Bharat at IIT Madras, created by fine-tuning OpenAI's open-source Whisper architecture on Indian-language speech data.

How it was built: Trained on 10.7 thousand hours of speech spanning 12 Indian languages, drawing on datasets including Kathbath (read speech collected via the Karya Android app, sourced from Wikipedia and news text) among others curated under the Vistaar benchmark project.

Performance: Evaluated across 59 language-domain benchmark combinations against other publicly available and commercial ASR systems, IndicWhisper produced the lowest word error rate in 39 of the 59 cases, with an average WER improvement of 4.1 points.

Practical note for this project: As of 2026, the official IndicWhisper checkpoints are gated on Hugging Face (requiring an access request rather than an instant download). A practical open alternative for initial development is the vasista22 family of Whisper-large-v2 fine-tunes for Telugu, Tamil, and Hindi, released under a permissive Apache 2.0 license and trained on comparable source data — usable immediately while an official IndicWhisper access request is pending. Government-backed Bhasini APIs are a further fallback offering free-for-noncommercial ASR/TTS/translation for 22 scheduled languages.

Why chosen over alternatives: General-purpose ASR (standard Whisper, Google Speech-to-Text) performs poorly on Indian languages and code-switched speech (a query that mixes Hindi and English mid-sentence, extremely common in real usage) — this is precisely the gap Indic-specific fine-tuning closes.

Links: AI4Bharat IndicWhisper model page — https://ai4bharat.iitm.ac.in/areas/model/ASR/IndicWhisper · Vistaar/IndicWhisper code and benchmark repo — https://github.com/AI4Bharat/vistaar · Community-hosted IndicWhisper checkpoint (MIT-licensed mirror) — https://huggingface.co/parthiv11/indic_whisper_nodcil · Original OpenAI Whisper (base architecture) — https://github.com/openai/whisper · vasista22 Whisper fine-tunes — Tamil: https://huggingface.co/vasista22/whisper-tamil-large-v2 · Telugu: https://huggingface.co/vasista22/whisper-telugu-large-v2 (search "vasista22" on Hugging Face for the full language set including Hindi) · Bhasini/open-source voice AI overview — https://caller.digital/blog/open-source-voice-ai-india-sarvam-ai4bharat-bhasini-2026


### 4.2 LangChain + RAG (eligibility reasoning)

What it is: LangChain is an open-source framework for building applications that chain together language model calls, retrieval systems, and external tools. In this project it implements retrieval-augmented generation: instead of asking an LLM to answer from its own training data (which risks fabricating scheme details, a serious problem when the answer affects someone's application decision), the system first retrieves the actual, current scheme text from an indexed database, and instructs the LLM to answer only using that retrieved text.

Components needed: a text embedding model (to convert scheme text and user queries into comparable vector representations — a multilingual sentence-embedding model is required here, since queries may arrive in a regional language while scheme documents are in English), a vector database (FAISS or Chroma, both open-source and suitable for a project of this scale) to store and search those embeddings, and an LLM to generate the final grounded answer.

Why RAG specifically, not a fine-tuned or general LLM: Government scheme rules change; a model fine-tuned on last year's scheme data would confidently give outdated answers. RAG allows the underlying scheme database to be updated independently of the model, and — critically — allows the system to say "I don't have information on that" rather than fabricating an answer when nothing relevant is retrieved, which is essential for a system citizens may rely on for real decisions.

Links: LangChain repository — https://github.com/langchain-ai/langchain · FAISS (vector search library) — https://github.com/facebookresearch/faiss · Chroma (vector database, alternative to FAISS) — https://github.com/chroma-core/chroma · Sentence-Transformers (multilingual embedding models) — https://github.com/UKPLab/sentence-transformers · Ollama (for running the open-weight LLM locally) — https://github.com/ollama/ollama


### 4.3 Tesseract OCR (document verification)

What it is: A long-established, open-source optical character recognition engine, capable of extracting machine-readable text from photographed or scanned documents.

Role in this project: Extracts structured fields (name, date of birth, address, income figure, category) from photographs of documents the citizen already possesses, removing the need for them to manually type or verbally state these details.

Known limitation to plan for: Tesseract's out-of-the-box accuracy on handwritten or poor-quality photographed Indian documents (skewed angles, glare, low-resolution phone cameras) is meaningfully lower than on clean printed text. Image pre-processing (deskewing, contrast normalization, cropping to the relevant field region) before OCR, and a confirmation step where the extracted field is shown/read back to the citizen for a yes/no confirmation, are both necessary design elements, not optional polish.

Link: https://github.com/tesseract-ocr/tesseract


### 4.4 Indic-TTS (speech synthesis)

What it is: AI4Bharat's text-to-speech project, producing natural-sounding synthetic speech across Indian languages, built from a mix of web-crawled and curated speech datasets.

Role in this project: Converts the system's final, text-based eligibility answer into spoken audio in the citizen's own language, completing the voice-in, voice-out loop so a citizen never has to read anything.

Links: Original Indic-TTS repository (13 languages, FastPitch + HiFi-GAN) — https://github.com/AI4Bharat/Indic-TTS · IndicF5 (newer, 2025, near-human quality, 11 languages) — https://github.com/AI4Bharat/IndicF5 · Indic Parler-TTS (HuggingFace/AI4Bharat collaboration, 21 languages) — https://huggingface.co/ai4bharat/indic-parler-tts


### 4.5 The LLM reasoning layer

What it is: An open-weight large language model (Llama or Mistral family, run via Ollama for local/self-hosting) that performs the actual reasoning step inside the RAG pipeline — deciding which retrieved scheme text is relevant to the query, what eligibility facts are still missing, and how to phrase the final answer in plain, actionable language.

Why open-weight rather than a commercial API: avoids recurring per-query API costs, which matters for a system intended to serve citizens at scale for free, and keeps sensitive query and document data from being sent to a third-party API — relevant given the eligibility documents involved are personal financial/identity data.


## 5. Integration Architecture — How the Components Connect

The four components above do not know about each other by default — they are independent tools. The integration work is building the orchestration layer that passes data between them correctly. All AI processing (speech-to-text, RAG reasoning, OCR, text-to-speech) runs on the backend server, not on the phone — the React Native app itself only handles audio/photo capture, playback, and UI, communicating with the backend purely through API calls:

Audio to text: the native app records audio locally, then sends it to a backend endpoint wrapping the IndicWhisper (or vasista22 fallback) model, returning transcribed text plus a language tag and confidence score.

Text to retrieval query: the transcribed text is embedded using a multilingual sentence-embedding model, and the resulting vector queries the FAISS/Chroma index of scheme documents, returning the top-k most relevant scheme entries.

Retrieval to reasoning: the retrieved scheme text, the original transcribed query, and (if this is a follow-up) the recent conversation history are assembled into a prompt sent to the LLM via LangChain's RAG chain, which returns a structured response identifying candidate schemes and any missing eligibility facts.

Document to structured facts: when the app requests a document photo, the image is sent to a backend endpoint wrapping Tesseract, which returns extracted key-value fields (field name → value, plus a per-field confidence score).

Facts to eligibility decision: a dedicated eligibility-matching module (not itself an ML model — a deterministic rules engine) takes the LLM-identified candidate schemes plus the OCR-extracted facts and evaluates each scheme's eligibility criteria against those facts, producing the final ranked, justified result. Keeping this step deterministic rather than another LLM call is a deliberate design choice — the actual eligibility decision should be auditable and rule-based, not a black-box language model guess.

Result to speech: the final ranked result is formatted into a natural-language response template and sent to Indic-TTS, returning audio for playback.

All of these steps are orchestrated by a single backend service (FastAPI recommended — see tech stack below) that exposes one endpoint per stage internally, but a single conversational endpoint externally, so the mobile app only needs to manage a simple back-and-forth audio/response exchange without knowing about the internal pipeline.


## 6. Complete Tech Stack

Layer

Technology

Purpose

Link

Speech-to-text

AI4Bharat IndicWhisper

Transcribe spoken queries

https://ai4bharat.iitm.ac.in/...

Embeddings

Multilingual Sentence-Transformers

Convert text to vectors

https://github.com/UKPLab/...

Vector database

FAISS or Chroma

Store scheme embeddings

https://github.com/chroma-core/...

RAG orchestration

LangChain

Chain retrieval and LLM

https://github.com/langchain-ai/...

LLM

Llama/Mistral via Ollama

Reason over scheme text

https://github.com/ollama/...

Document OCR

Tesseract

Field extraction from photos

https://github.com/tesseract-ocr/...

Text-to-speech

AI4Bharat Indic-TTS

Convert answer to audio

https://github.com/AI4Bharat/...


## 7. Requirements

7.1 Functional requirements

FR1: The system shall accept a spoken query in at least two supported languages (recommend starting with Hindi plus one additional regional language relevant to your region, expanding later).

FR2: The system shall transcribe the spoken query to text with a measurable word error rate, and shall prompt for re-recording if transcription confidence falls below a defined threshold.

FR3: The system shall retrieve relevant government schemes from an indexed corpus using the transcribed query.

FR4: The system shall request and process a photograph of a supporting document, extracting relevant structured fields via OCR.

FR5: The system shall confirm extracted document fields with the citizen (yes/no) before using them in an eligibility decision.

FR6: The system shall cross-reference extracted facts against retrieved scheme eligibility rules and produce a ranked, justified eligibility result.

FR7: The system shall convert the final result into spoken output in the same language as the original query.

FR8: The system shall support at least one round of follow-up conversational question without losing prior context.

FR9: The system shall provide a fallback path to a nearest Common Service Centre or helpline when it cannot resolve a query with sufficient confidence.

FR10: The system shall log interactions (with explicit citizen consent) to support evaluation and continuous improvement.

7.2 Non-functional requirements

Performance: end-to-end response time (voice query to spoken answer) should be targeted under roughly 8-10 seconds on a typical mid-range Android device over a 4G connection — acceptable for a conversational tool used deliberately, not a real-time assistant.

Usability: the interface must be usable by someone with no prior smartphone app experience — large touch targets, minimal text, icon-first navigation, and voice as the primary interaction mode throughout, not just for the initial query.

Accuracy and reliability: the RAG pipeline must be evaluated for hallucination — cases where the LLM states something not actually present in the retrieved scheme text — and must default to "I don't have clear information on that, please visit your nearest Common Service Centre" rather than guessing.

Language coverage: start with a small, well-supported set of languages rather than attempting all 12+ IndicWhisper-supported languages in a first version; expand only after the core pipeline is validated.

Data privacy and security: personal document images and extracted identity/income data must be encrypted in transit and at rest, retained only as long as needed for the session (or as long as the citizen consents to for improvement purposes), and never sent to third-party services without explicit disclosure — see Section 9.

Maintainability: government scheme rules change periodically; the scheme corpus and its vector index need a defined refresh process, not a one-time scrape.

Offline/low-connectivity tolerance: since target users are disproportionately in areas with weaker connectivity, the app should degrade gracefully — a recorded query that can't reach the backend immediately is queued in on-device local storage (SQLite) and retried automatically, with a clear "waiting to send" state shown to the citizen, rather than the interaction being lost or failing silently.

App size and device compatibility: the installable APK should stay reasonably small and run on Android versions still common on budget devices in the target user base (not just the latest Android release), since all AI inference (STT, RAG, OCR, TTS) happens on the backend — the app itself stays a lightweight client, not a heavy on-device ML app.


## 8. Dataset Requirements

Dataset

Source

Purpose

Access notes

Scheme eligibility corpus

Scraped and structured from myscheme.gov.in (https://www.myscheme.gov.in/) — 2,300+ schemes across 15 categories as of the platform's most recent public figures

Core knowledge base for the RAG retrieval layer

Not offered as a clean downloadable dataset — requires a genuine scraping and structuring effort; budget real project time for this, and plan to re-scrape periodically since scheme data changes

Speech-to-text models

AI4Bharat IndicWhisper (gated access) — https://ai4bharat.iitm.ac.in/areas/model/ASR/IndicWhisper — or vasista22 Whisper fine-tunes (open, Apache 2.0) — https://huggingface.co/vasista22

Pretrained ASR — no training from scratch required

Request IndicWhisper access early; use the open alternative to avoid blocking early development

Text-to-speech models

AI4Bharat Indic-TTS — https://github.com/AI4Bharat/Indic-TTS

Pretrained TTS — no training from scratch required

Public on GitHub/Hugging Face

Evaluation query set

Self-constructed: a set of realistic spoken queries in target languages, recorded by volunteers (classmates, family members willing to help), paired with the correct expected eligibility outcome

Measuring end-to-end accuracy, not just individual component accuracy

Fully self-contained, no external dependency

OCR test documents

Self-created mock ration card / income certificate / ID images (not real people's actual identity documents)

Testing and demonstrating the OCR pipeline without privacy risk

Avoid using genuine personal identity documents belonging to real people, including your own, in any shared or submitted materials

RAG evaluation set

A set of question-answer pairs manually constructed from actual myScheme scheme pages (https://www.myscheme.gov.in/), used to check whether the RAG pipeline retrieves and reasons correctly

Measuring retrieval and hallucination rate

Self-constructed, tied directly to the scraped scheme corpus

9. Privacy, Security, and Compliance

This project processes identity and income-related personal data, which brings it squarely within the scope of India's Digital Personal Data Protection Act, 2023 (DPDP Act) and its associated 2025 Rules. This is genuinely relevant to your report, not a boilerplate mention:

Consent: the Act requires consent to be free, specific, informed, and given through a clear affirmative action — no pre-ticked boxes or assumed consent. The app must explicitly ask the citizen's permission before capturing a document photo or storing any interaction log, in plain language, in their own spoken language if possible.

Purpose limitation and data minimization: only the specific fields needed for eligibility checking (age, income bracket, category, etc.) should be extracted and retained — not the full document image, once the required fields are confirmed, unless the citizen separately consents to longer retention for app-improvement purposes.

Storage limitation: data should be deleted once its stated purpose is served, consistent with the Act's requirement that data collected for a purpose be erased once that purpose is achieved or consent is withdrawn.

Security safeguards: the Act and its 2025 Rules require reasonable security measures and mandate breach reporting with no minimum-severity threshold — meaning even a small data exposure must be handled seriously in your system design (encryption in transit/at rest, access logging).

Special note for a college project: to keep the project itself squarely within safe and simple compliance during development, avoid collecting real citizens' documents at all during build and testing — use self-created mock documents (Section 8) and only consider a real-user pilot, with a proper consent flow, as a later extension once the core system is validated.

Official and reference documents:

Full Act text (PDF, MeitY) — https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf

DPDP Rules 2025, official press release (PIB) — https://www.pib.gov.in/PressReleasePage.aspx?PRID=2190655

DPDP Act, 2023 — overview — https://en.wikipedia.org/wiki/Digital_Personal_Data_Protection_Act,_2023

DPDP Rules, 2025 — overview — https://en.wikipedia.org/wiki/Digital_Personal_Data_Protection_Rules,_2025

Data minimization requirements analysis (Lexology) — https://www.lexology.com/library/detail.aspx?g=c448a81d-dbb7-4c9d-9071-c6ae7d83b4cb

Data minimization requirements analysis (S&R Associates) — https://www.snrlaw.in/navigating-data-minimization-requirements-under-indias-dpdp-act/

Plain-language DPDP explainer — https://www.matters.ai/compliance/dpdp/dpdp-act-2023

DPDP Act key analysis (consent provisions) — https://www.lightbeam.ai/resources/blogs/indian-digital-personal-data-protection-act-2023-analysis/

10. Complete Feature List

Core features (needed for a working demo)

Single-tap voice query capture

Multi-language speech-to-text (start with 2 languages)

RAG-grounded scheme retrieval and reasoning

Document photo capture and OCR field extraction

Field confirmation step (citizen confirms extracted data is correct)

Deterministic eligibility matching against scheme rules

Ranked, justified eligibility results

Text-to-speech playback of results in the citizen's language

Basic conversational follow-up (one round of context-aware follow-up question)

Fallback message directing to nearest Common Service Centre when confidence is low

Extended features (strong additions if time allows)

Multi-turn conversation memory across several follow-up questions

Auto-fill of a scheme's application form using already-extracted document data

A simple admin interface for re-running the scheme-corpus scrape and rebuilding the vector index

Offline-tolerant design: queued audio upload and retry on poor connectivity

A visual (not just spoken) results screen as a secondary channel for citizens who can read some text, alongside the voice-first primary path

Basic usage analytics dashboard (aggregated, privacy-respecting) showing which scheme categories are most queried, useful for your evaluation chapter

Explicitly out of scope for a first version

Actual submission of scheme applications on the citizen's behalf (myScheme itself does not yet support this for most schemes; the app should link/direct rather than attempt to submit)

Support for all 12+ Indian languages IndicWhisper covers — start narrow, expand later

Real-time, sub-second response — the target is a deliberate conversational pace, not instant response

11. Evaluation Plan

To give this project a genuine, measurable "research" component rather than just a working demo, plan to report on:

ASR accuracy: word error rate on your self-recorded evaluation query set, per language.

Retrieval accuracy: for your constructed RAG evaluation set, what fraction of queries retrieve the actually-correct scheme(s) in the top-k results.

Hallucination rate: manually reviewing a sample of generated answers against the retrieved source text to check the LLM did not state anything not actually supported by that text.

OCR field-extraction accuracy: per-field accuracy on your mock document test set, and separately on real-world-quality photos (angled, poorly lit) versus clean scans, to honestly characterize the gap.

End-to-end task success rate: for a full evaluation query set, what fraction of queries result in a correct, complete, spoken eligibility answer without needing escalation.

Usability: even a small, informal usability session (a handful of volunteers unfamiliar with the app, asked to complete a realistic query) gives you qualitative material for your report that a purely technical evaluation won't.

12. Suggested Timeline

Milestone (per your department schedule)

Target for this project

Title submission (Aug 20)

Finalize scope: 2 languages, core pipeline, myScheme corpus subset

Mid Progress Report (Sept 5)

Scheme corpus scraped and structured; IndicWhisper/vasista22 integrated and tested standalone

Mid-Term Report & Viva (Sept 10-26)

RAG retrieval pipeline working end-to-end on text queries (voice integration in progress); literature survey and formal requirements finalized

Final Progress Report (Oct 30)

Full voice-to-voice pipeline working, including OCR and eligibility matching; evaluation data collection underway

Final Report & Viva (Nov 18-25)

Evaluation results complete (ASR/retrieval/OCR/end-to-end accuracy); polished demo; full report and diary of supervisor meetings

13. Mapping to the Complex Engineering Problem Classification

WP1 (fundamentals-based analysis): the RAG grounding design, embedding/retrieval tuning, and eligibility rule modeling all require genuine engineering reasoning, not just API calls.

WP2 (wide-ranging technical and non-technical issues): this project directly involves societal (digital divide), legal (DPDP Act compliance), and economic (which schemes citizens can access) dimensions simultaneously.

WP4 (novel/infrequently encountered problem): the specific combination of voice-first, document-verified, RAG-grounded scheme eligibility does not exist as a deployed system.

EA1 (diverse resources): speech models, language models, OCR, structured government data, and citizen-facing UX design all have to be brought together.

EA3 (creative, research-based solution): the integration architecture and the eligibility-matching design are original engineering work built on, but not copied from, existing components.

EA4 (significant consequences, hard to predict/mitigate): an incorrect eligibility answer has real consequences for a citizen's access to entitlements — this is exactly the kind of high-stakes, hard-to-fully-test system the classification is meant to capture, and your report should discuss this honestly rather than only presenting best-case results.

14. Risks and Honest Limitations

Scheme corpus staleness: government schemes change; a snapshot scraped in September will drift out of date by November. State this explicitly as a known limitation rather than letting an evaluator find it themselves.

OCR accuracy on real-world document photos: expect meaningfully lower accuracy than on clean test images; report this gap honestly rather than only showing best-case numbers.

Gated model access: if IndicWhisper access approval is delayed, the vasista22 fallback keeps the project unblocked — decide this early rather than losing time waiting.

LLM hallucination: even with RAG grounding, occasional incorrect statements are possible; your hallucination-rate evaluation (Section 11) should be presented as a real, measured limitation, not glossed over.

Not a replacement for official channels: the report should frame this system as an accessibility layer that extends and complements myScheme and Common Service Centres, not a system claiming legal authority over eligibility determinations.

15. Full Reference List

Bhogale, K.S., Sundaresan, S., Raman, A., Javed, T., Khapra, M.M., Kumar, P. (2023). Vistaar: Diverse Benchmarks and Training Sets for Indian Language ASR. arXiv:2305.15386. https://arxiv.org/abs/2305.15386

AI4Bharat, IIT Madras — IndicWhisper, Indic-TTS, and related Indic NLP/speech projects. https://ai4bharat.iitm.ac.in/

National Sample Survey Office, 78th Round (2020-21) — computer literacy statistics, as cited in "Digital literacy and E-government in India" (2025/2026). https://www.humanitiesjournal.net/archives/2026/vol8issue1/PartA/8-1-8-950.pdf

"Examining the Role of Digital India in Rural Development" (2025) — survey-based ranking of barriers to digital scheme access. https://www.researchgate.net/publication/395530377_Examining_the_Role_of_Digital_India_in_Rural_Development

"Design and implementation of digital literacy training programme: Findings of a quasi-experimental study from rural India," PLOS Digital Health (2025). https://journals.plos.org/digitalhealth/article?id=10.1371%2Fjournal.pdig.0000617

myScheme — National Platform for Government Schemes, National e-Governance Division, MeitY, Government of India. https://www.myscheme.gov.in/

The Digital Personal Data Protection Act, 2023 (No. 22 of 2023). https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf

The Digital Personal Data Protection Rules, 2025, Government of India. https://www.pib.gov.in/PressReleasePage.aspx?PRID=2190655

Tesseract OCR — open-source OCR engine. https://github.com/tesseract-ocr/tesseract

LangChain — open-source framework for LLM application orchestration. https://github.com/langchain-ai/langchain

FAISS — vector search library. https://github.com/facebookresearch/faiss

Chroma — vector database. https://github.com/chroma-core/chroma

Sentence-Transformers — multilingual embedding models. https://github.com/UKPLab/sentence-transformers

Ollama — local LLM serving. https://github.com/ollama/ollama

OpenAI Whisper — base ASR architecture. https://github.com/openai/whisper

vasista22 — Whisper Indic-language fine-tunes (Hugging Face). https://huggingface.co/vasista22/whisper-tamil-large-v2

AI4Bharat Indic-TTS GitHub. https://github.com/AI4Bharat/Indic-TTS

AI4Bharat IndicF5 GitHub. https://github.com/AI4Bharat/IndicF5

AI4Bharat Indic Parler-TTS (Hugging Face). https://huggingface.co/ai4bharat/indic-parler-tts

