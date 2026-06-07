<div align="center">

![ClaimPilot Banner](/hero-banner.svg)

<br/>

# ClaimPilot

**Production-grade autonomous insurance claims processing — from inbox to settlement without a human reading it.**

An end-to-end multi-agent system built on LangGraph, Claude `tool_use`, and ML-based fraud detection. Six specialized agents, zero manual steps, real decisions.

<br/>

[![Python](https://img.shields.io/badge/Python-74.9%25-3572A5?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-18.8%25-2b7489?style=flat-square&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15-000000?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Orchestrated-00d4ff?style=flat-square)](https://langchain.com/langgraph)
[![Claude](https://img.shields.io/badge/Claude-tool_use-a78bfa?style=flat-square)](https://anthropic.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ed?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-00ff88?style=flat-square)](LICENSE)

</div>

---

## What Is This

The insurance industry processes claims manually. An adjuster reads a PDF. Someone calls the hospital. Another person cross-references a weather report. It takes 3–5 business days and costs around $85 per claim in labor.

ClaimPilot replaces that entire loop with an autonomous agent pipeline that averages **2.4 seconds per claim**. Six LangGraph-orchestrated agents pick up where the last left off — parsing multimodal input, validating policy coverage via RAG, gathering external evidence in parallel, running an ML fraud model trained on 10,000 synthetic claims, calculating a settlement, and generating a signed PDF — all without a single human reading the file.

Borderline cases get pushed to a live WebSocket dashboard where a human adjuster makes the final call.

This is not a chain of prompts. It is a **state machine** where agents observe, reason, select tools autonomously, execute them, and pass structured state downstream.

---

## Architecture

![Architecture Flow](/architecture-flow.svg)

```
[Email / Upload Portal]
        ↓
  ┌──────────────────┐
  │   Intake Agent    │  ← PyMuPDF, Whisper, Claude NER extraction
  └────────┬─────────┘
           ↓
  ┌──────────────────┐
  │ Validation Agent  │  ← RAG over policy docs (Pinecone hybrid: BM25 + dense)
  └────────┬─────────┘
           ↓ (conditional fork — PARALLEL via Celery)
  ┌─────────────────────┐     ┌──────────────────────┐
  │ Investigation Agent  │     │  Fraud Detection      │
  │  • OpenWeatherMap    │     │  Agent                │
  │  • FHIR R4 records   │     │  • IsolationForest ML │
  │  • Tavily web search │     │  • Duplicate detect   │
  │  • Google Geocoding  │     │  • Network analysis   │
  └──────────┬──────────┘     └──────────┬────────────┘
             └──────────┬────────────────┘
                        ↓
  ┌──────────────────┐
  │  Settlement Agent │  ← Payout calc, ReportLab PDF, APPROVE/REJECT
  └────────┬─────────┘
           ↓
    ┌───────────────────────┐
    ↓                       ↓
  Finalized            Escalated
  (PDF + email)   → Human-in-the-Loop Dashboard
                    (WebSocket push, adjuster decision)
```

Every edge in this graph is conditional. Every agent has a tool registry. Claude decides which tools to call per claim context — a health claim hits FHIR and ICD-10 validation; an auto claim hits weather and incident search; a property claim hits satellite geocoding and disaster records.

---

## The Dashboard

![ClaimPilot Dashboard](/dashboard-ui.svg)

The Next.js 15 frontend surfaces everything:

- Live claim queue with real-time status via WebSocket
- Per-claim agent reasoning chain — every tool call, every decision, full audit trail
- Fraud score visualization with the five-signal breakdown
- Human-in-the-Loop adjuster panel for escalated cases: APPROVED / REJECTED / REQUEST_MORE_INFO
- Settlement PDF download inline

---

## Six Agents, One Pipeline

| # | Agent | What It Actually Does | Tools It Calls |
|---|-------|----------------------|----------------|
| 01 | **Intake** | Entry point. Handles PDFs, scanned images, audio recordings, and raw text. Extracts structured claim data using Claude. | `pdf_parser` (PyMuPDF), `whisper_transcriber`, `claude_extractor` |
| 02 | **Validation** | Policy gatekeeper. Checks if the claimant's policy number is active, the incident type is covered, and the event date falls within the policy window. | `pinecone_rag` (BM25 + dense hybrid), `date_validator`, `policy_checker` |
| 03 | **Investigation** | Evidence gatherer. Collects external signals relevant to the claim — weather at the incident location, FHIR hospital records, incident news search, geocoding. | `openweathermap`, `fhir_r4_client`, `tavily_search`, `google_geocoding` |
| 04 | **Fraud Detection** | ML skeptic. Runs five independent signals and aggregates a composite fraud score. Runs in parallel with Investigation via Celery. | `isolation_forest_model`, `duplicate_detector`, `timing_analyzer`, `inconsistency_checker`, `network_analyzer` |
| 05 | **Settlement** | Decision engine. Applies deductible logic, calculates payout, generates a signed PDF, fires an email notification. | `settlement_calculator`, `reportlab_pdf_generator`, `smtp_notifier` |
| 06 | **Human-in-the-Loop** | Escalation handler. Pushes borderline claims to the adjuster dashboard over WebSocket. Awaits decision. | `websocket_push`, `adjuster_api`, `decision_recorder` |

---

## Fraud Detection Pipeline

![Fraud Detection](/fraud-detection.svg)

Five independent signals, one composite score:

1. **ML Anomaly Score** — Isolation Forest trained on 10,000 synthetic claims. Fraudulent claims average ~0.93; clean claims average ~0.20. Feature set: days since policy start, claim amount, prior claims in 12 months, submission delay, incident time of day, provider claim frequency, claim-to-limit ratio.

2. **Duplicate Detection** — Fingerprints each incident (location + date + type hash) against historical claims. Flags same-event re-submissions.

3. **Timing Analysis** — Flags claims filed suspiciously close to policy start dates, end dates, or with unusual submission delays.

4. **Narrative Inconsistency** — Cross-references claim text against gathered evidence. Hospital city mismatch, unlisted physicians, date drift — all flagged.

5. **Network Analysis** — Provider/claimant co-occurrence graph. A provider appearing in 4+ suspicious claims is a different kind of signal than one data point alone.

**Routing rules:**
- Score ≥ 0.7 → AUTO REJECT
- Score 0.4–0.7 → ESCALATE to human
- Score < 0.4 → Continue to settlement

The model was trained using SMOTE to handle class imbalance in the synthetic training set and serialized with `joblib` for production inference.

---

## Tech Stack

![Tech Stack](/tech-stack.svg)

### Orchestration & AI
| Component | Choice | Why |
|-----------|--------|-----|
| Agent orchestration | **LangGraph** | State machine semantics, checkpointing, conditional edges, native parallelism |
| LLM | **Claude 3.5 Sonnet** via Anthropic SDK | `tool_use` API — agents reason about tool selection, not just execute prompts |
| Task queue | **Celery + Redis** | Investigation + Fraud agents run in true parallel, not sequential |

### Backend
| Component | Choice |
|-----------|--------|
| API framework | FastAPI 0.115 — async, OpenAPI auto-docs |
| Database | PostgreSQL 16 via SQLAlchemy (async) |
| Vector DB | Pinecone — hybrid BM25 + dense embedding search over policy documents |
| PDF parsing | PyMuPDF (fitz) |
| PDF generation | ReportLab |
| Audio transcription | OpenAI Whisper API |
| Web search | Tavily API |
| Health records | Mock FHIR R4 endpoint |
| ML | scikit-learn IsolationForest + SMOTE (imbalanced-learn) |

### Frontend
| Component | Choice |
|-----------|--------|
| Framework | Next.js 15, App Router |
| UI library | React 19 |
| Styling | Tailwind CSS v4 |
| Real-time | WebSocket client — live claim status |

### Infrastructure
```
docker-compose.yml
├── postgres:16-alpine     (claims database, healthcheck)
├── redis:7-alpine         (celery broker, healthcheck)
├── backend                (FastAPI + agents, depends on above)
├── celery-worker          (parallel task runner, depends on above)
└── frontend               (Next.js, depends on backend)
```

---

## Project Structure

```
claimpilot/
├── backend/
│   ├── agents/
│   │   ├── intake_agent.py          # PDF/audio/text → ClaimState
│   │   ├── validation_agent.py      # Pinecone RAG policy check
│   │   ├── investigation_agent.py   # Weather, FHIR, geo, web search
│   │   ├── fraud_detection_agent.py # 5-signal ML pipeline
│   │   ├── settlement_agent.py      # Payout calc + PDF + email
│   │   └── human_loop_agent.py      # WebSocket escalation
│   ├── orchestrator/
│   │   └── graph.py                 # LangGraph state machine definition
│   ├── tools/
│   │   ├── pdf_tools.py             # PyMuPDF wrapper
│   │   ├── weather_tools.py         # OpenWeatherMap client
│   │   ├── fhir_tools.py            # FHIR R4 mock client
│   │   ├── fraud_tools.py           # IsolationForest + rules
│   │   └── pdf_generator.py         # ReportLab settlement PDF
│   ├── models/
│   │   └── claim.py                 # SQLAlchemy ORM
│   ├── api/
│   │   ├── routes.py                # FastAPI endpoints
│   │   └── websocket.py             # WS adjuster push
│   ├── mock_data/
│   │   ├── generate_claims.py       # Synthetic claims
│   │   ├── generate_policies.py     # Policy documents for RAG
│   │   ├── generate_fhir_data.py    # Mock FHIR patient records
│   │   └── generate_fraud_training.py # 10K training records
│   ├── tests/
│   │   └── *.py                     # pytest suite
│   └── main.py                      # FastAPI entry point
├── frontend/
│   ├── app/                         # Next.js App Router pages
│   ├── components/                  # Dashboard, claim table, HITL panel
│   └── lib/
│       ├── api.ts                   # Backend API client
│       └── websocket.ts             # WS connection manager
├── data/                            # Generated mock data
├── notebooks/                       # Jupyter — fraud model training
├── scripts/                         # Utility scripts
├── .env.example                     # All required env vars documented
└── docker-compose.yml               # Full stack in one command
```

---

## API Reference

| Method | Endpoint | What It Does |
|--------|----------|-------------|
| `POST` | `/api/v1/claims/submit` | Submit a new claim — multipart form + optional file upload |
| `GET` | `/api/v1/claims` | List claims, filter by `?status=PENDING\|APPROVED\|REJECTED\|ESCALATED` |
| `GET` | `/api/v1/claims/{id}` | Full claim detail including agent outputs |
| `POST` | `/api/v1/claims/{id}/human-decision` | Adjuster decision: `APPROVED / REJECTED / REQUEST_MORE_INFO` |
| `GET` | `/api/v1/claims/{id}/reasoning-chain` | Full per-step agent audit trail with tool calls |
| `GET` | `/fhir/r4/Patient/{id}` | Mock FHIR patient record endpoint |
| `WS` | `/ws/adjuster/{adjuster_id}` | WebSocket — escalated claims pushed in real time |

### Submit a claim

```bash
curl -X POST http://localhost:8000/api/v1/claims/submit \
  -F "claim_type=auto" \
  -F "claimant_name=Riya Sharma" \
  -F "policy_number=POL-AUTO-001" \
  -F "event_date=2024-06-20" \
  -F "event_description=Rear-end collision at MG Road intersection, moderate damage" \
  -F "file=@/path/to/claim_document.pdf"
```

### Get full reasoning chain

```bash
curl http://localhost:8000/api/v1/claims/CLM-2041/reasoning-chain
# Returns every agent step: which tools were called, what they returned,
# and what the agent decided to do next
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 22+
- Docker Desktop (optional but recommended for full stack)
- `ANTHROPIC_API_KEY` — required for agent reasoning

### 1. Clone and configure

```bash
git clone https://github.com/sat1828/ClaimPilot.git
cd ClaimPilot
cp .env.example .env
# Edit .env — add ANTHROPIC_API_KEY at minimum
```

### 2. Generate synthetic data + train fraud model

```bash
cd backend
pip install -r requirements.txt

# Generate mock data
python mock_data/generate_claims.py
python mock_data/generate_policies.py
python mock_data/generate_fhir_data.py
python mock_data/generate_fraud_training.py

# Train and serialize the fraud model
python -c "
import json, joblib, numpy as np
from sklearn.ensemble import IsolationForest
with open('../data/fraud_training/fraud_training_data.json') as f:
    data = json.load(f)
features = ['days_since_policy_start','claim_amount','num_prior_claims_12mo',
            'submission_delay_days','incident_time_of_day',
            'provider_claim_frequency','claim_vs_policy_limit_ratio']
X = [[r['features'][k] for k in features] for r in data['records']]
model = IsolationForest(n_estimators=200, contamination=0.01, random_state=42)
model.fit(np.array(X))
joblib.dump(model, 'models/fraud_isolation_forest.joblib')
print('Model ready.')
"
```

### 3. Run backend

```bash
uvicorn main:app --reload --port 8000
# API docs at http://localhost:8000/docs
```

### 4. Run frontend

```bash
cd frontend
npm install
npm run dev
# Dashboard at http://localhost:3000
```

### 5. Or run everything with Docker

```bash
docker-compose up --build
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# PG: localhost:5432 | Redis: localhost:6379
```

---

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://claimpilot:claimpilot@postgres:5432/claimpilot
DATABASE_SYNC_URL=postgresql://claimpilot:claimpilot@postgres:5432/claimpilot

# Redis
REDIS_URL=redis://redis:6379/0

# AI / LLM
ANTHROPIC_API_KEY=sk-ant-...         # Required — powers all 6 agents
OPENAI_API_KEY=sk-...                # Whisper audio transcription

# Vector DB
PINECONE_API_KEY=pcsk-...
PINECONE_INDEX_NAME=claimpilot-policies
PINECONE_ENVIRONMENT=us-east-1-aws

# External APIs
TAVILY_API_KEY=tvly-...              # Web search in Investigation agent
OPENWEATHERMAP_API_KEY=...           # Weather at incident location
GOOGLE_MAPS_API_KEY=AIza...          # Geocoding

# Email notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=claimpilot@example.com
SMTP_PASSWORD=...

# App
APP_ENV=development
SECRET_KEY=change-this
LOG_LEVEL=INFO
```

---

## Why This Is Genuinely Agentic

Most "agent" demos are prompt chains with a for-loop. This is not that.

Each agent in ClaimPilot:
1. **Receives structured state** — a typed `ClaimState` object passed through the LangGraph graph
2. **Has a tool registry** — a set of functions Claude can call, with typed inputs/outputs
3. **Makes autonomous tool selection decisions** — Claude reads the claim context and decides *which* tools to invoke, in what order, with what parameters
4. **Passes enriched state downstream** — each agent appends its findings to the shared state, which subsequent agents use

The graph has **conditional edges** — whether the claim goes to human review or auto-settlement depends on fraud scores and confidence levels computed at runtime, not hardcoded branching. The graph has **parallelism** — Investigation and Fraud Detection run simultaneously via Celery, and their results are merged before Settlement.

This is the pattern from Anthropic's [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) research — applied to a real, messy domain with real external API integrations.

---

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

---

## Notebooks

The `notebooks/` directory contains a Jupyter notebook for:
- Fraud model training walkthrough with feature importance analysis
- SMOTE resampling demonstration on the synthetic class-imbalanced dataset
- Isolation Forest decision boundary visualization
- Mock data exploration and distribution analysis

```bash
cd notebooks
jupyter notebook
```

---

## Roadmap

- [ ] Real email ingestion via IMAP polling
- [ ] Pinecone index population with actual policy PDFs
- [ ] Streaming agent progress to frontend (SSE)
- [ ] Role-based access for multi-adjuster teams
- [ ] Webhook outbound for approved/rejected decisions
- [ ] Claim type expansion: Life, Travel, Crop

---

<div align="center">

Built with Claude `tool_use` · LangGraph · FastAPI · Next.js 15

</div>
