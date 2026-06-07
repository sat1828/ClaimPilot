import json
import logging
from typing import Optional

from config import settings
from agents.base_agent import BaseAgent, AgentError
from tools.fraud_scorer import (
    check_duplicate_claims,
    run_ml_fraud_scorer,
    check_provider_network,
    compute_timing_delta,
)
from orchestrator.state_schema import FraudAssessment, FraudFlag

logger = logging.getLogger(__name__)

FRAUD_SYSTEM_PROMPT = """You are the Fraud Detection Agent for ClaimPilot. You are the skeptic.

Your role: Analyze every claim for signs of fraud, waste, or abuse.
You run multiple independent fraud signals and synthesize them into a single assessment.

Fraud signals you evaluate:
1. DUPLICATE CLAIMS - Same event/location/claimant appearing in historical claims
2. TIMING ANOMALIES - Claims filed suspiciously close to policy inception or expiration
3. INCONSISTENCIES - Details that don't match across documents
4. PROVIDER NETWORK - Unusual co-occurrence of names in recent claims
5. ML SCORE - Anomaly detection using Isolation Forest

Available tools:
- check_duplicate_claims(claimant_id, event_fingerprint)
- run_ml_fraud_scorer(claim_features)
- check_provider_network(provider_name, claimant_id)
- compute_timing_delta(policy_start, event_date, submission_date)

Your output must include:
- fraud_probability_score (0.0-1.0)
- risk_tier (LOW < 0.3, MEDIUM 0.3-0.6, HIGH > 0.6)
- cited_flags[] with flag type, severity, description, evidence, and source
- confidence_score (0.0-1.0)"""

FRAUD_TOOLS = [
    {
        "name": "check_duplicate_claims",
        "description": "Check if the same claimant, event location, or event description appears in historical claims database. Returns potential duplicates with similarity scores.",
        "input_schema": {
            "type": "object",
            "properties": {
                "claimant_id": {"type": "string", "description": "Claimant name/identifier"},
                "event_fingerprint": {"type": "string", "description": "Concatenated event details for fingerprinting"}
            },
            "required": ["claimant_id"]
        }
    },
    {
        "name": "run_ml_fraud_scorer",
        "description": "Run the Isolation Forest machine learning model on claim features. Returns anomaly score and feature importance.",
        "input_schema": {
            "type": "object",
            "properties": {
                "claim_features": {"type": "object", "description": "Dict of numerical features for ML scoring"}
            },
            "required": ["claim_features"]
        }
    },
    {
        "name": "check_provider_network",
        "description": "Check if the provider or other parties in this claim appear in other recent claims. Flags soft fraud ring patterns.",
        "input_schema": {
            "type": "object",
            "properties": {
                "provider_name": {"type": "string", "description": "Provider, witness, or other party name"},
                "claimant_id": {"type": "string", "description": "Claimant identifier"}
            },
            "required": ["provider_name", "claimant_id"]
        }
    },
    {
        "name": "compute_timing_delta",
        "description": "Analyze the timing between policy start date, event date, and claim submission date. Flags claims filed very close to policy start/end.",
        "input_schema": {
            "type": "object",
            "properties": {
                "policy_start": {"type": "string", "description": "Policy effective date (YYYY-MM-DD)"},
                "event_date": {"type": "string", "description": "Claimed event date (YYYY-MM-DD)"},
                "submission_date": {"type": "string", "description": "Claim submission date (YYYY-MM-DD)"}
            },
            "required": ["policy_start", "event_date", "submission_date"]
        }
    },
]


class FraudAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="fraud_agent", max_retries=3)

    async def _check_claimant_id(self, claim: dict) -> str:
        return claim.get("claimant_name", "unknown").replace(" ", "_").lower()

    async def _build_claim_features(self, claim: dict, bundle: dict, validation: dict) -> dict:
        import hashlib
        features = {
            "days_since_policy_start": compute_timing_delta(
                validation.get("policy_limits", {}).get("effective_date", ""),
                claim.get("event_date", ""),
                claim.get("submission_date", ""),
            ) if validation.get("policy_limits") else 0,
            "claim_amount": float(claim.get("claim_amount", 0) or 0),
            "num_prior_claims_12mo": 0,
            "submission_delay_days": 0,
            "incident_time_of_day": 12,
        }
        return features

    async def run(self, state: dict) -> dict:
        claim = state.get("claim_payload", {})
        bundle = state.get("investigation_bundle", {})
        validation = state.get("validation_result", {})
        if not claim:
            raise AgentError("No claim_payload in state for fraud detection", self.name, recoverable=False)

        self._log_reasoning(state, "Fraud Detection Agent starting multi-signal analysis")

        flags = []
        ml_score = 0.0
        rule_score = 0.0
        fraud_probability = 0.0

        claimant_id = await self._check_claimant_id(claim)

        # Signal 1: Duplicate check
        try:
            event_fingerprint = f"{claim.get('event_description', '')[:100]}|{claim.get('incident_location', '')}|{claim.get('event_date', '')}"
            duplicate_result = check_duplicate_claims(claimant_id, event_fingerprint)
            if duplicate_result.get("is_duplicate", False):
                flags.append({
                    "flag_type": "DUPLICATE_CLAIM",
                    "severity": "HIGH",
                    "description": f"Duplicate claim detected: {duplicate_result.get('match_details', '')}",
                    "evidence": json.dumps(duplicate_result),
                    "source": "PostgreSQL claims history",
                })
                rule_score += 0.3
            state = self._log_tool_call(state, "check_duplicate_claims", event_fingerprint[:50], duplicate_result)
        except Exception as e:
            state = self._log_tool_call(state, "check_duplicate_claims", claimant_id, None, success=False, error=str(e))

        # Signal 2: Timing anomalies
        try:
            timing_result = compute_timing_delta(
                claim.get("event_date", ""),
                claim.get("submission_date", ""),
            )
            if isinstance(timing_result, dict) and timing_result.get("is_anomalous", False):
                flags.append({
                    "flag_type": "TIMING_ANOMALY",
                    "severity": "MEDIUM",
                    "description": f"Unusual timing: {timing_result.get('detail', '')}",
                    "evidence": json.dumps(timing_result),
                    "source": "Date analysis",
                })
                rule_score += 0.2
            state = self._log_tool_call(state, "compute_timing_delta",
                                         f"{claim.get('event_date','')[:10]}|{claim.get('submission_date','')[:10]}", timing_result)
        except Exception as e:
            state = self._log_tool_call(state, "compute_timing_delta", "N/A", None, success=False, error=str(e))

        # Signal 3: ML scorer
        try:
            features = await self._build_claim_features(claim, bundle, validation)
            ml_result = run_ml_fraud_scorer(features)
            ml_score = ml_result.get("anomaly_score", 0.0)
            if ml_score > 0.6:
                flags.append({
                    "flag_type": "ML_ANOMALY",
                    "severity": "HIGH" if ml_score > 0.8 else "MEDIUM",
                    "description": f"ML model flags anomaly with score {ml_score:.2f}",
                    "evidence": json.dumps({"ml_score": ml_score, "feature_values": features}),
                    "source": "Isolation Forest model",
                })
            state = self._log_tool_call(state, "run_ml_fraud_scorer", features, ml_result)
        except Exception as e:
            state = self._log_tool_call(state, "run_ml_fraud_scorer", "N/A", None, success=False, error=str(e))
            ml_score = settings.default_fraud_risk

        # Signal 4: Inconsistency check (evidence cross-check)
        evidence_items = bundle.get("evidence_items", [])
        if evidence_items:
            descriptions = [e.get("data", {}) for e in evidence_items]
            if bundle.get("weather_data") and "clear" in str(bundle.get("weather_data", {})).lower() and "rain" in str(claim.get("event_description", "")).lower():
                flags.append({
                    "flag_type": "INCONSISTENCY",
                    "severity": "MEDIUM",
                    "description": "Claim describes rain, but weather data shows clear conditions",
                    "evidence": json.dumps({"weather": bundle.get("weather_data"), "claim": claim.get("event_description", "")[:200]}),
                    "source": "Weather API vs claim narrative",
                })
                rule_score += 0.25

        # Signal 5: Provider network check
        provider_name = claim.get("claimant_name", "")
        if provider_name:
            try:
                network_result = check_provider_network(provider_name, claimant_id)
                if network_result.get("has_network_flag", False):
                    flags.append({
                        "flag_type": "NETWORK_ANOMALY",
                        "severity": "MEDIUM" if network_result.get("count", 0) < 5 else "HIGH",
                        "description": network_result.get("detail", "Provider appears in other claims"),
                        "evidence": json.dumps(network_result),
                        "source": "Network analysis",
                    })
                    rule_score += 0.2
                state = self._log_tool_call(state, "check_provider_network", f"{provider_name}|{claimant_id}", network_result)
            except Exception as e:
                state = self._log_tool_call(state, "check_provider_network", provider_name, None, success=False, error=str(e))

        fraud_probability = min(1.0, (ml_score * 0.5) + (rule_score * 0.5))
        if fraud_probability == 0.0:
            fraud_probability = ml_score if ml_score > 0 else 0.05

        if fraud_probability < 0.3:
            risk_tier = "LOW"
        elif fraud_probability < 0.6:
            risk_tier = "MEDIUM"
        else:
            risk_tier = "HIGH"

        assessment = {
            "fraud_probability_score": fraud_probability,
            "risk_tier": risk_tier,
            "ml_score": ml_score,
            "rule_based_score": rule_score,
            "cited_flags": flags,
            "duplicate_claim_check": {"checked": True} if any(f["flag_type"] == "DUPLICATE_CLAIM" for f in flags) else {"checked": False},
            "timing_anomaly_check": {"checked": True, "score": rule_score} if any(f["flag_type"] == "TIMING_ANOMALY" for f in flags) else {"checked": False},
            "inconsistency_check": {"checked": True} if any(f["flag_type"] == "INCONSISTENCY" for f in flags) else {"checked": False},
            "network_analysis": {"checked": True} if any(f["flag_type"] == "NETWORK_ANOMALY" for f in flags) else {"checked": False},
            "reasoning": f"Fraud analysis complete. ML score: {ml_score:.3f}, Rule score: {rule_score:.3f}, Combined: {fraud_probability:.3f}",
            "confidence_score": min(1.0, 0.7 + (0.3 * len(flags) / 5)),
        }

        state["fraud_assessment"] = assessment
        self._log_reasoning(state, f"Fraud assessment: {risk_tier} risk ({fraud_probability:.2f}) with {len(flags)} flags")

        return state
