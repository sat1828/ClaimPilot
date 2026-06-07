import json
import logging
import uuid
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import JSONResponse

from config import settings
from api.claims import router as claims_router
from api.ws import router as ws_router
from tools.fhir_mock import query_fhir_records, lookup_icd10_code, _MOCK_PATIENTS

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ClaimPilot API starting up")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Claude model: {settings.claude_model}")
    yield
    logger.info("ClaimPilot API shutting down")


app = FastAPI(
    title="ClaimPilot API",
    description="Autonomous Insurance Claims Processing Agent",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(claims_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/ws")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ClaimPilot",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/fhir/r4/Patient/{patient_id}")
async def fhir_patient(patient_id: str):
    result = query_fhir_records(patient_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return JSONResponse(content=result["patient"])


@app.get("/fhir/r4/Patient/{patient_id}/Encounter")
async def fhir_patient_encounters(patient_id: str):
    result = query_fhir_records(patient_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return JSONResponse(content={"resourceType": "Bundle", "type": "searchset", "entry": result.get("encounters", [])})


@app.get("/fhir/r4/Patient")
async def fhir_patient_search(name: str = ""):
    if name:
        name_lower = name.lower()
        for pid, patient in _MOCK_PATIENTS.items():
            full = f"{patient['name'][0]['given'][0]} {patient['name'][0]['family']}"
            if name_lower in full.lower():
                return JSONResponse(content=patient)
    return JSONResponse(content=list(_MOCK_PATIENTS.values()))


@app.get("/fhir/r4/Claim/{claim_id}")
async def fhir_claim(claim_id: str):
    for pid, claims_list in _MOCK_CLAIMS_FHIR.items():  # type: ignore
        for c in claims_list:
            if c.get("id") == claim_id:
                return JSONResponse(content=c)
    raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")


@app.get("/api/v1")
async def api_root():
    return {
        "service": "ClaimPilot API v1",
        "endpoints": {
            "claims": "/api/v1/claims",
            "claim_detail": "/api/v1/claims/{id}",
            "submit_claim": "/api/v1/claims/submit",
            "health": "/health",
            "websocket": "/ws/adjuster/{adjuster_id}",
        },
    }
