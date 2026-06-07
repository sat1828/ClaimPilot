import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def push_to_dashboard(case_summary: dict, adjuster_id: str = "default-adjuster") -> bool:
    try:
        import asyncio
        logger.info(f"[DASHBOARD PUSH] Claim {case_summary.get('claim_number', 'N/A')} → Adjuster {adjuster_id}")
        logger.debug(f"Case summary: {json.dumps(case_summary, indent=2, default=str)[:500]}...")
        return True
    except Exception as e:
        logger.error(f"Failed to push to dashboard: {e}")
        return False


def record_human_decision(claim_id: str, decision: str, adjuster_notes: str = "") -> dict:
    logger.info(f"[HUMAN DECISION] Claim {claim_id} → {decision}")
    if adjuster_notes:
        logger.info(f"Adjuster notes: {adjuster_notes[:200]}")
    return {
        "claim_id": claim_id,
        "decision": decision,
        "adjuster_notes": adjuster_notes,
        "recorded": True,
    }


def send_email_notification(recipient: str, subject: str, body: str) -> bool:
    from config import settings
    if settings.smtp_user and settings.smtp_password:
        try:
            import smtplib
            from email.mime.text import MIMEText
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = settings.claim_inbox_email
            msg["To"] = recipient
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)
            logger.info(f"Email sent to {recipient}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    else:
        logger.info(f"[MOCK EMAIL] To: {recipient}, Subject: {subject}, Body preview: {body[:100]}...")
        return True
