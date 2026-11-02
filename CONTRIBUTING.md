# YojanaVaani — Team Collaboration & Contribution Guide 🤝

Welcome to the **YojanaVaani** repository! This document establishes the collaboration standards, branching model, and local setup instructions for our 3-person team.

---

## 👥 1. Team Tracks & Workstream Ownership

To avoid stepping on each other's toes and minimize git merge conflicts, project responsibilities are divided into three clear tracks:

| Track | Primary Modules | Key Responsibilities |
|---|---|---|
| **Track 1: Backend & Agent Orchestration** | `/backend/app/api`, `/backend/app/services/agent.py`, `/backend/app/mcp/` | LangGraph agent loop, MCP statutory tools, FastAPI endpoints, ASR/TTS services, PostgreSQL session logic. |
| **Track 2: Mobile Client & Native Modules** | `/mobile/src/screens/`, `/mobile/src/services/`, `/mobile/android/` | React Native UI screens, Kotlin `AudioRecorderModule`, offline SQLite queuing, audio playback, permission flows. |
| **Track 3: Data Pipeline, Vision & Evaluation** | `/data-pipeline/`, `/backend/app/services/ocr_service.py`, `/backend/evaluation/` | Scheme scraping/normalizing, ChromaDB vector indexing, OpenCV + Tesseract OCR extraction, benchmark evaluation suite. |

---

## 🌿 2. Git Branching Strategy (GitHub Flow + Develop)

We follow a clean, structured branching strategy:

```
[main]          ── (Protected: Production / Viva release only)
   ▲
   │ (Merged after testing)
[develop]       ── (Active Integration Branch)
   ▲        ▲        ▲
   │        │        │
[feature/backend-*] [feature/mobile-*] [feature/data-*]
```

### 📌 Branch Hierarchy
1. **`main`**: Production-ready branch. **Never commit directly to `main`**. Merges into `main` happen only when a phase or release milestone is fully tested.
2. **`develop`**: The primary integration branch. All feature branches branch off from `develop` and merge back into `develop` via Pull Requests.
3. **`feature/<track>-<short-description>`**: Individual feature branches created by each teammate for specific tasks.
   - Examples:
     - `feature/backend-rate-limiting`
     - `feature/mobile-waveform-animation`
     - `feature/data-khasra-regex`
4. **`fix/<short-description>`**: Quick bugfix branches branched off `develop`.

---

## 🚀 3. Daily Team Workflow

### Step 1: Clone the Repo (For New Teammates)
```bash
git clone https://github.com/Nikita-Gupta-19/YojanaVaani.git
cd YojanaVaani

# Switch to the develop branch
git checkout develop
```

### Step 2: Start a New Task
Always pull the latest changes from `develop` before starting new work:
```bash
git checkout develop
git pull origin develop

# Create your feature branch
git checkout -b feature/<track>-<task-name>
```

### Step 3: Local Development & Pre-Commit Verification
Before staging or committing, ensure tests pass locally:
```bash
# 1. Run backend tests
cd backend
source .venv/bin/activate
pytest tests/

# 2. Run mobile tests (from repo root)
cd ../mobile
npm test
```

### Step 4: Commit with Clear Messages
Follow Conventional Commits:
```bash
git add <files-you-changed>
git commit -m "feat(mobile): add animated mic ripple effect during recording"
```
Prefixes:
- `feat(...)`: A new feature or screen
- `fix(...)`: A bugfix
- `test(...)`: Adding or updating test cases
- `docs(...)`: Updating markdown or report files
- `refactor(...)`: Code cleanup without behavior change

### Step 5: Push and Open a Pull Request (PR)
```bash
git push -u origin feature/<track>-<task-name>
```
1. Go to [github.com/Nikita-Gupta-19/YojanaVaani](https://github.com/Nikita-Gupta-19/YojanaVaani).
2. Open a Pull Request targeting **`base: develop`** (NOT `main`).
3. Fill out the PR template checklist.
4. Have at least one other teammate review and approve before merging!

---

## ⚙️ 4. Local Environment Setup

### Backend & Database Setup
```bash
# 1. Start PostgreSQL with Docker
docker compose up -d postgres

# 2. Setup Python environment (Python 3.10+)
cd backend
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env if using custom database credentials or Ollama URLs

# 4. Run database migrations
alembic upgrade head

# 5. Start development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Mobile App Setup (React Native CLI)
```bash
cd mobile
npm install

# Start Metro bundler
npm start

# In a separate terminal, launch Android app (ensure emulator or device is connected)
npm run android
```

---

## ⚠️ 5. Non-Negotiable Academic & Engineering Rules

All 3 teammates must strictly follow these constraints (from `AGENTS.md`):

1. **Eligibility Decisions are NEVER Made by LLMs**:
   - `check_eligibility` must always be deterministic Python rules logic (`EligibilityEngine`). The LLM decides *when* to call the tool, never the verdict itself.
2. **Forbidden Libraries**:
   - **TensorFlow, Keras, MATLAB** are strictly forbidden across all branches (course requirement). Use PyTorch, torchvision, and OpenCV instead.
3. **All AI Inference is Server-Side**:
   - The React Native mobile client is strictly a capture and playback client. Never embed models, STT, OCR, or RAG logic inside the mobile app.
4. **Data Privacy (DPDP Act 2023)**:
   - **Never** commit real identity documents (Aadhaar cards, ration cards, income certificates). Use synthetic mock files in `/backend/data/mock_documents/` only.
   - Never commit `.env` or API secrets.

---

## 📞 6. Quick Communication & Escalation
- If you encounter a database schema conflict or need to modify shared schemas (`Scheme`, `ConversationState`), discuss with the team before running new Alembic migrations.
- If you find a breaking change in API response shapes, notify the mobile lead immediately.
