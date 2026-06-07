# ClaimPilot

> **Autonomous Insurance Claims Processing Agent**
> *"From inbox to settlement — without a human reading it."*

A production-grade multi-agent system that processes insurance claims end-to-end using LangGraph orchestration, Claude `tool_use`, and ML-based fraud detection.

## Architecture

```
[Email / Upload Portal]
        ↓
  ┌─────────────────┐
  │   Intake Agent   │  ← PDF parsing, audio transcription, text extraction
  └────────┬────────┘
           ↓
  ┌─────────────────┐
  │ Validation Agent │  ← RAG over policy docs (Pinecone hybrid search)
  └────────┬────────┘
           ↓
  ┌──────────────────┐     ┌─────────────────────┐
  │ Investigation     │     │  Fraud Detection     │  ← Parallel (Celery)
  │ Agent             │     │  Agent               │
  │  • Weather API    │     │  • ML anomaly score  │
  │  • FHIR records   │     │  • Rule-based checks │
  │  • Incident lookup│     │  • Network analysis  │
  │  • Geocoding      │     │  • Duplicate detect  │
  └────────┬──────────┘     └──────────┬──────────┘
           └──────────┬────────────────┘
                      ↓
  ┌─────────────────┐
  │ Settlement Agent │  ← Calculates payout, generates PDF
  └────────┬────────┘
           ↓
    ┌──────────┴──────────┐
    ↓                     ↓
  Finalized           Escalated
  (APPROVE/REJECT)    → Human-in-the-Loop Dashboard
```

## 6 Specialized Agents

| Agent | Role | Tools |
|-------|------|-------|
| **Intake** | Entry point - parse multimodal input | PDF parser, Whisper, Claude extraction |
| **Validation** | Gatekeeper - policy eligibility | Pinecone RAG, date validation |
| **Investigation** | Detective - gather external evidence | Weather API, FHIR, incident search, geocoding |
| **Fraud Detection** | Skeptic - ML + rule-based scoring | Isolation Forest, duplicate detection, network analysis |
| **Settlement** | Decision-maker - calculate & decide | Settlement calculator, PDF generator |
| **Human-in-the-Loop** | Escalation handler | WebSocket push, adjuster dashboard |

## Quick Start

### Prerequisites
- Python 3.11+, Node.js 22+
- Docker Desktop (optional, for full stack)

### 1. Clone & Environment
```bash
cp .env.example .env
# Edit .env and add your API keys (ANTHROPIC_API_KEY is required for agents)
```

### 2. Backend
```bash
cd backend
pip install -r requirements.txt
python -m pytest tests/ -v     # Run tests

# Generate mock data
python mock_data/generate_claims.py
python mock_data/generate_policies.py
python mock_data/generate_fhir_data.py
python mock_data/generate_fraud_training.py

# Train fraud model (Jupyter notebook alternative)
python -c "
import json, joblib, numpy as np
from sklearn.ensemble import IsolationForest
with open('../data/fraud_training/fraud_training_data.json') as f:
    data = json.load(f)
X = [[r['features'][k] for k in ['days_since_policy_start','claim_amount','num_prior_claims_12mo',
     'submission_delay_days','incident_time_of_day','provider_claim_frequency','claim_vs_policy_limit_ratio']]
     for r in data['records']]
model = IsolationForest(n_estimators=200, contamination=0.01, random_state=42).fit(np.array(X))
joblib.dump(model, 'models/fraud_isolation_forest.joblib')
print('Model trained')
"

uvicorn main:app --reload --port 8000
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

### 4. Docker (Full Stack)
```bash
docker-compose up --build
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/claims/submit` | Submit a new claim (form data + file upload) |
| `GET` | `/api/v1/claims` | List all claims (optional `?status=` filter) |
| `GET` | `/api/v1/claims/{id}` | Get full claim detail |
| `POST` | `/api/v1/claims/{id}/human-decision` | Adjuster decision (APPROVED/REJECTED/REQUEST_MORE_INFO) |
| `GET` | `/api/v1/claims/{id}/reasoning-chain` | Full agent audit trail |
| `GET` | `/fhir/r4/Patient/{id}` | Mock FHIR patient records |
| `WS` | `/ws/adjuster/{id}` | WebSocket for live case push |

### Submit a Claim
```bash
curl -X POST http://localhost:8000/api/v1/claims/submit \
  -F "claim_type=auto" \
  -F "claimant_name=John Doe" \
  -F "policy_number=POL-AUTO-001" \
  -F "event_date=2024-06-20" \
  -F "event_description=Rear-end collision at Main St intersection"
```

## Tech Stack

- **Orchestration**: LangGraph (state machine, checkpointing, conditional edges)
- **LLM**: Claude `tool_use` (Anthropic SDK)
- **Backend**: FastAPI, Celery + Redis, SQLAlchemy + PostgreSQL
- **Frontend**: Next.js 15, React 19, Tailwind v4, WebSocket
- **ML**: scikit-learn Isolation Forest, SMOTE
- **Vector DB**: Pinecone hybrid search (BM25 + dense)
- **PDF**: PyMuPDF (parsing), ReportLab (generation)
- **Infrastructure**: Docker Compose

## Fraud Detection

The fraud detection pipeline uses 5 independent signals:
1. **ML Anomaly Score** — Isolation Forest trained on 10K synthetic claims
2. **Duplicate Detection** — Event fingerprint matching against historical claims
3. **Timing Analysis** — Flags claims filed suspiciously close to policy start/end
4. **Inconsistency Check** — Cross-references claim narrative with gathered evidence
5. **Network Analysis** — Detects provider/claimant co-occurrence patterns

**Model performance** (on synthetic test set): Fraudulent claims score ~0.93, legitimate claims ~0.20.

## Project Structure

```
claimpilot/
├── backend/
│   ├── agents/           # 6 specialized agents
│   ├── orchestrator/     # LangGraph state machine
│   ├── tools/            # Tool wrappers (weather, FHIR, PDF, etc.)
│   ├── models/           # SQLAlchemy ORM models
│   ├── api/              # FastAPI routes + WebSocket
│   ├── mock_data/        # Synthetic data generators
│   ├── tests/            # pytest test suite
│   └── main.py           # FastAPI app entry point
├── frontend/
│   ├── app/              # Next.js App Router pages
│   ├── components/       # Dashboard components
│   └── lib/              # API + WebSocket clients
├── data/                 # Generated mock data
├── notebooks/            # Jupyter notebooks
└── docker-compose.yml
```

## Why This Is Genuinely Agentic

Each agent has **tools** and makes **autonomous decisions** about which tools to use based on claim context:

- A car accident claim triggers: weather API, police report search, damage estimation
- A medical claim triggers: FHIR hospital records, ICD-10 validation, prescription history
- A property claim triggers: satellite geocoding, disaster records, local incident check

This is not a chain of prompts. It is a **state machine** where agents observe, reason, select tools, execute them, and pass structured state downstream — exactly the pattern described in Anthropic's agentic systems guidelines.
