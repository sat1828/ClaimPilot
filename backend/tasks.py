import json
import logging

from celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def run_pipeline(claim_data: dict) -> dict:
    import asyncio
    from orchestrator.pipeline import pipeline

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(pipeline.run(claim_data))
        logger.info(f"Pipeline completed: {result.get('claim_id')}")
        return result
    except Exception as exc:
        logger.error(f"Pipeline failed: {exc}")
        raise
    finally:
        loop.close()


@celery_app.task
def process_claim_file(file_path: str) -> dict:
    import asyncio
    import uuid
    from datetime import datetime
    from orchestrator.pipeline import pipeline
    from tools.pdf_parser import parse_pdf

    text = parse_pdf(file_path)
    claim_id = str(uuid.uuid4())
    claim_number = f"CP-{datetime.utcnow().strftime('%Y%m%d')}-{claim_id[:8].upper()}"

    initial_state = {
        "claim_id": claim_id,
        "claim_number": claim_number,
        "raw_input": {"type": "pdf", "content": text, "file_path": file_path},
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

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(pipeline.run(initial_state))
        return result
    finally:
        loop.close()
