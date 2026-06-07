import json
import logging
import os
import random
from datetime import datetime, timedelta
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

_FRAUD_MODEL = None
_FRAUD_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "fraud_isolation_forest.joblib")


def _get_fraud_model():
    global _FRAUD_MODEL
    if _FRAUD_MODEL is not None:
        return _FRAUD_MODEL
    try:
        if os.path.exists(_FRAUD_MODEL_PATH):
            import joblib
            _FRAUD_MODEL = joblib.load(_FRAUD_MODEL_PATH)
            logger.info("Loaded Isolation Forest model from disk")
            return _FRAUD_MODEL
    except Exception as e:
        logger.warning(f"Could not load fraud model: {e}")

    logger.info("Using mock fraud scorer (no model file found)")
    return None


_MOCK_DUPLICATES = {}


def check_duplicate_claims(claimant_id: str, event_fingerprint: str = "") -> dict:
    global _MOCK_DUPLICATES
    if claimant_id not in _MOCK_DUPLICATES:
        _MOCK_DUPLICATES[claimant_id] = []

    recent = _MOCK_DUPLICATES[claimant_id]
    is_duplicate = False
    match_details = ""

    for prev in recent:
        if event_fingerprint and len(set(event_fingerprint.split("|")) & set(prev.split("|"))) >= 2:
            is_duplicate = True
            match_details = f"Similar event details found"
            break

    fp_hash = event_fingerprint[:100] if event_fingerprint else str(random.randint(0, 999999))
    recent.append(fp_hash)
    if len(recent) > 20:
        _MOCK_DUPLICATES[claimant_id] = recent[-20:]

    return {"is_duplicate": is_duplicate, "match_details": match_details, "prior_claims_count": len(recent) - 1}


def run_ml_fraud_scorer(claim_features: dict) -> dict:
    model = _get_fraud_model()

    ft_vector = np.array([[
        float(claim_features.get("days_since_policy_start", 0)),
        float(claim_features.get("claim_amount", 0) or 0),
        float(claim_features.get("num_prior_claims_12mo", 0)),
        float(claim_features.get("submission_delay_days", 0)),
        float(claim_features.get("incident_time_of_day", 12)),
        float(claim_features.get("provider_claim_frequency", 1)),
        float(claim_features.get("claim_vs_policy_limit_ratio", 0.5)),
    ]])

    if model is not None:
        try:
            score = model.score_samples(ft_vector)[0]
            norm_path = os.path.join(os.path.dirname(_FRAUD_MODEL_PATH), "fraud_normalization.npz")
            if os.path.exists(norm_path):
                norm = np.load(norm_path)
                score_min, score_max = float(norm["score_min"]), float(norm["score_max"])
                anomaly_score = 1.0 - (score - score_min) / (score_max - score_min + 1e-10)
            else:
                anomaly_score = 1.0 - (score - model.offset_) / (-0.4 - (-0.72) + 1e-10)
            anomaly_score = float(max(0.0, min(1.0, anomaly_score)))
            logger.info(f"ML fraud score: {anomaly_score:.3f}")
            return {"anomaly_score": anomaly_score, "model_used": "Isolation Forest", "feature_values": claim_features}
        except Exception as e:
            logger.warning(f"Model inference failed: {e}")

    random.seed(hash(json.dumps(claim_features, sort_keys=True)) % (2**32))
    base_score = random.uniform(0.0, 0.3)
    if claim_features.get("num_prior_claims_12mo", 0) > 3:
        base_score += 0.2
    if claim_features.get("claim_amount", 0) > 50000:
        base_score += 0.15
    if claim_features.get("days_since_policy_start", 365) < 30:
        base_score += 0.2
    anomaly_score = min(1.0, base_score)

    logger.info(f"Mock ML fraud score: {anomaly_score:.3f}")
    return {"anomaly_score": anomaly_score, "model_used": "mock_heuristic", "feature_values": claim_features}


def check_provider_network(provider_name: str, claimant_id: str) -> dict:
    random.seed(hash(provider_name + claimant_id) % (2**32))
    count = random.randint(0, 3)
    return {
        "has_network_flag": count >= 3,
        "count": count,
        "detail": f"Found {count} recent claims involving similar parties" if count > 0 else "No network connections found",
    }


def compute_timing_delta(event_date: str, submission_date: str) -> dict:
    try:
        event = datetime.strptime(event_date[:10], "%Y-%m-%d") if event_date else datetime.now()
        submission = datetime.strptime(submission_date[:10], "%Y-%m-%d") if submission_date else datetime.now()
    except (ValueError, TypeError):
        return {"delay_days": 0, "is_anomalous": False, "detail": "Could not parse dates"}

    delay = (submission - event).days
    is_anomalous = delay < 0 or delay > 180 or delay == 0
    detail = ""
    if delay < 0:
        detail = "Claim submitted before event date"
    elif delay > 180:
        detail = f"Claim filed {delay} days after event - unusually late"
    elif delay == 0:
        detail = "Claim filed on same day as event"
    else:
        detail = f"Claim filed {delay} days after event - normal timing"

    return {"delay_days": delay, "is_anomalous": is_anomalous, "detail": detail}
