import logging
from celery import Celery
from config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "claimpilot",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=300,
    task_time_limit=600,
)


@celery_app.task(bind=True, max_retries=3)
def run_pipeline_task(self, claim_data: dict) -> dict:
    import asyncio
    from orchestrator.pipeline import pipeline

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(pipeline.run(claim_data))
        logger.info(f"Celery pipeline completed: {result.get('claim_id')}")
        return result
    except Exception as exc:
        logger.error(f"Celery pipeline failed: {exc}")
        raise self.retry(exc=exc, countdown=60)
    finally:
        loop.close()


@celery_app.task
def run_investigation_task(claim_data: dict) -> dict:
    import asyncio
    from agents.investigation_agent import InvestigationAgent

    agent = InvestigationAgent()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(agent.run(claim_data))
        return result
    finally:
        loop.close()


@celery_app.task
def run_fraud_task(claim_data: dict) -> dict:
    import asyncio
    from agents.fraud_agent import FraudAgent

    agent = FraudAgent()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(agent.run(claim_data))
        return result
    finally:
        loop.close()
