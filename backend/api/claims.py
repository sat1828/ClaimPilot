import json
import logging
import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from config import settings
from orchestrator.pipeline import pipeline
from orchestrator.state_schema import ClaimState

logger = logging.getLogger(__name__)

router = APIRouter(tags=["claims"])

_active_pipelines: dict[str, dict] = {}


class ClaimSubmitRequest(BaseModel):
    claim_type: str = Field(..., description="Type of claim: auto, medical, property, travel, etc.")
    claimant_name: str = Field(..., description="Full name of the claimant")
    claimant_email: str = Field("", description="Claimant email address")
    policy_number: str = Field(..., description="Insurance policy number")
    event_date: str = Field(..., description="Date of the incident (YYYY-MM-DD)")
    event_description: str = Field(..., description="Description of what happened")
    incident_location: str = Field("", description="Where the incident occurred")
    claim_amount: float = Field(0.0, description="Total claim amount in USD")


@router.post("/claims/submit")
async def submit_claim(
    background_tasks: BackgroundTasks,
    claim_type: str = Form(...),
    claimant_name: str = Form(...),
    claimant_email: str = Form(""),
    policy_number: str = Form(...),
    event_date: str = Form(...),
    event_description: str = Form(...),
    incident_location: str = Form(""),
    claim_amount: float = Form(0.0),
    file: Optional[UploadFile] = File(None),
):
    data = ClaimSubmitRequest(
        claim_type=claim_type,
        claimant_name=claimant_name,
        claimant_email=claimant_email,
        policy_number=policy_number,
        event_date=event_date,
        event_description=event_description,
        incident_location=incident_location,
        claim_amount=claim_amount,
    )

    claim_id = str(uuid.uuid4())
    claim_number = f"CP-{datetime.utcnow().strftime('%Y%m%d')}-{claim_id[:8].upper()}"

    raw_input = {
        "type": "text",
        "content": json.dumps({
            "claim_type": data.claim_type,
            "claimant_name": data.claimant_name,
            "claimant_email": data.claimant_email,
            "policy_number": data.policy_number,
            "event_date": data.event_date,
            "event_description": data.event_description,
            "incident_location": data.incident_location,
            "claim_amount": data.claim_amount,
        }),
    }

    if file and file.filename:
        upload_dir = os.path.join("data", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        safe_filename = f"{claim_id}_{os.path.basename(file.filename)}"
        file_path = os.path.join(upload_dir, safe_filename)
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        ext = file.filename.lower().rsplit(".", 1)[-1]
        if ext in ("pdf",):
            raw_input["type"] = "pdf"
        elif ext in ("mp3", "wav", "m4a", "ogg"):
            raw_input["type"] = "audio"
        raw_input["file_path"] = file_path
        raw_input["content"] = ""

    initial_state = {
        "claim_id": claim_id,
        "claim_number": claim_number,
        "raw_input": raw_input,
        "claim_payload": {},
        "validation_result": {},
        "investigation_bundle": {},
        "fraud_assessment": {},
        "settlement_decision": {},
        "reasoning_chain": [],
        "current_status": "SUBMITTED",
        "current_agent": "",
        "error_log": [],
        "retry_count": {},
        "pipeline_started_at": datetime.utcnow().isoformat(),
        "pipeline_completed_at": "",
    }

    _active_pipelines[claim_id] = dict(initial_state)

    async def run_pipeline():
        try:
            result = await pipeline.run(dict(initial_state))
            _active_pipelines[claim_id] = result
            logger.info(f"Pipeline completed for {claim_number}: {result.get('current_status')}")
        except Exception as e:
            logger.error(f"Pipeline failed for {claim_number}: {e}")
            state = dict(initial_state)
            state["current_status"] = "FAILED"
            state["error_log"] = [str(e)]
            _active_pipelines[claim_id] = state

    background_tasks.add_task(run_pipeline)

    return {
        "claim_id": claim_id,
        "claim_number": claim_number,
        "status": "SUBMITTED",
        "message": "Claim submitted. Pipeline processing started.",
    }


@router.get("/claims")
async def list_claims(status: Optional[str] = None):
    results = []
    for cid, state in _active_pipelines.items():
        if status and state.get("current_status", "").upper() != status.upper():
            continue
        results.append({
            "claim_id": cid,
            "claim_number": state.get("claim_number", "N/A"),
            "claimant_name": state.get("claim_payload", {}).get("claimant_name", "N/A"),
            "claim_type": state.get("claim_payload", {}).get("claim_type", "N/A"),
            "status": state.get("current_status", "UNKNOWN"),
            "current_agent": state.get("current_agent", ""),
            "created_at": state.get("pipeline_started_at", ""),
        })
    return {"claims": results, "total": len(results)}


@router.get("/claims/{claim_id}")
async def get_claim(claim_id: str):
    state = _active_pipelines.get(claim_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")
    return {
        "claim_id": claim_id,
        "claim_number": state.get("claim_number", "N/A"),
        "claim_payload": state.get("claim_payload", {}),
        "validation_result": state.get("validation_result", {}),
        "investigation_bundle": state.get("investigation_bundle", {}),
        "fraud_assessment": state.get("fraud_assessment", {}),
        "settlement_decision": state.get("settlement_decision", {}),
        "reasoning_chain": state.get("reasoning_chain", []),
        "current_status": state.get("current_status", "UNKNOWN"),
        "current_agent": state.get("current_agent", ""),
        "error_log": state.get("error_log", []),
        "pipeline_started_at": state.get("pipeline_started_at", ""),
        "pipeline_completed_at": state.get("pipeline_completed_at", ""),
    }


@router.post("/claims/{claim_id}/human-decision")
async def human_decision(
    claim_id: str,
    decision: str = Form(...),
    adjuster_notes: str = Form(""),
):
    state = _active_pipelines.get(claim_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")

    valid_decisions = {"APPROVED", "REJECTED", "REQUEST_MORE_INFO"}
    if decision.upper() not in valid_decisions:
        raise HTTPException(status_code=400, detail=f"Decision must be one of: {', '.join(valid_decisions)}")
    final_decision = decision.upper()
    notes = adjuster_notes

    settlement = dict(state.get("settlement_decision", {}))
    settlement["decision"] = final_decision.upper()
    settlement["human_reviewed"] = True
    settlement["human_notes"] = notes
    chain = list(settlement.get("reasoning_chain", []))
    chain.append({"step": "human_decision", "result": final_decision.upper(), "notes": notes, "source": "HumanAdjuster"})
    settlement["reasoning_chain"] = chain

    state["settlement_decision"] = settlement
    state["current_status"] = final_decision.upper()
    _active_pipelines[claim_id] = state

    logger.info(f"Human decision for {claim_id}: {final_decision}")
    return {"claim_id": claim_id, "decision": final_decision, "status": "RECORDED"}


@router.get("/claims/{claim_id}/reasoning-chain")
async def get_reasoning_chain(claim_id: str):
    state = _active_pipelines.get(claim_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")
    return {"claim_id": claim_id, "reasoning_chain": state.get("reasoning_chain", [])}
