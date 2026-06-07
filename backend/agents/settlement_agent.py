import json
import logging
import os
from typing import Optional

import anthropic

from config import settings
from agents.base_agent import BaseAgent, AgentError
from tools.pdf_generator import generate_settlement_letter, render_decision_pdf
from orchestrator.state_schema import SettlementDecision

logger = logging.getLogger(__name__)

SETTLEMENT_SYSTEM_PROMPT = """You are the Settlement Agent for ClaimPilot. You are the decision-maker.

Your role: Calculate the settlement amount and render the final verdict based on all evidence gathered by previous agents.

You receive:
1. ClaimPayload - the original claim details
2. ValidationResult - policy coverage, limits, and exclusions
3. InvestigationBundle - all external evidence gathered
4. FraudAssessment - fraud probability score and flags

Your decision logic:
- APPROVE: fraud_probability < 0.3 AND evidence supports claim AND policy covers event
- REJECT: policy explicitly excludes event OR missing critical evidence
- ESCALATE: fraud_probability >= 0.3 OR ambiguous evidence OR low confidence

Settlement calculation:
- Start with documented losses from InvestigationBundle
- Apply policy deductible
- Check policy sub-limits
- Factor in depreciation if applicable
- Apply fraud risk adjustment if MEDIUM risk (reduce by 10%)

Generate:
1. A structured SettlementDecision with full reasoning chain
2. A professional settlement letter via generate_settlement_letter
3. Render as PDF via render_decision_pdf

Each decision step must cite its evidence source. Complete explainability is required."""

SETTLEMENT_TOOLS = [
    {
        "name": "calculate_settlement",
        "description": "Calculate the settlement amount based on policy limits, documented losses, and deductible. Returns the calculated payout.",
        "input_schema": {
            "type": "object",
            "properties": {
                "policy_data": {"type": "object", "description": "Policy coverage limits and deductible"},
                "losses": {"type": "array", "description": "List of documented losses with amounts"},
                "deductible": {"type": "number", "description": "Policy deductible amount"}
            },
            "required": ["policy_data", "losses", "deductible"]
        }
    },
    {
        "name": "generate_settlement_letter",
        "description": "Generate a professional settlement or rejection letter using Claude. Returns the letter text.",
        "input_schema": {
            "type": "object",
            "properties": {
                "decision": {"type": "string", "description": "APPROVE, REJECT, or ESCALATE"},
                "claimant_data": {"type": "object", "description": "Claimant name, address, policy info"},
                "decision_details": {"type": "object", "description": "Settlement amount, reasoning, next steps"}
            },
            "required": ["decision", "claimant_data"]
        }
    },
    {
        "name": "render_decision_pdf",
        "description": "Render the decision letter as a professional PDF using ReportLab. Returns the file path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text_content": {"type": "string", "description": "The full text of the decision letter"},
                "output_path": {"type": "string", "description": "Where to save the PDF file"}
            },
            "required": ["text_content", "output_path"]
        }
    },
]


class SettlementAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="settlement_agent", max_retries=3)
        self._client = None

    @property
    def client(self):
        if self._client is None:
            api_key = settings.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY", "dummy-key")
            self._client = anthropic.Anthropic(api_key=api_key)
        return self._client

    def _calculate_settlement(self, claim: dict, validation: dict, bundle: dict, fraud: dict) -> dict:
        deductible = float(validation.get("deductible", 500) or 500)
        claim_amount = float(claim.get("claim_amount", 0) or 0)
        fraud_probability = fraud.get("fraud_probability_score", 0.0)
        coverage_limit = float(validation.get("policy_limits", {}).get("coverage_limit", claim_amount * 2) or claim_amount * 2)

        losses = []
        for item in bundle.get("evidence_items", []):
            if isinstance(item.get("data"), dict) and "amount" in item["data"]:
                losses.append(item["data"])

        total_losses = claim_amount
        if not losses:
            losses.append({"description": claim.get("event_description", "Claimed loss")[:100], "amount": claim_amount})

        settlement = min(total_losses, coverage_limit)
        payout = max(0, settlement - deductible)

        if fraud_probability >= 0.3 and fraud_probability < 0.6:
            payout *= 0.9

        return {
            "settlement_amount": round(settlement, 2),
            "deductible_applied": deductible,
            "payout_amount": round(payout, 2),
            "policy_limits_used": {
                "coverage_limit": coverage_limit,
                "deductible": deductible,
            },
            "losses_assessed": losses,
        }

    def _decide(self, claim: dict, validation: dict, fraud: dict, calc: dict) -> tuple:
        fraud_probability = fraud.get("fraud_probability_score", 0.0)
        coverage_status = validation.get("coverage_status", "NOT_COVERED")
        confidence = min(
            validation.get("confidence_score", 1.0),
            fraud.get("confidence_score", 1.0),
        )

        if coverage_status in ("NOT_COVERED",):
            return "REJECT", "Policy does not cover this event type. See policy exclusions.", max(0.8, confidence)
        elif coverage_status == "PARTIALLY_COVERED":
            return "ESCALATE", "Partial coverage. Requires human review to determine applicability.", min(0.6, confidence)
        elif fraud_probability >= settings.fraud_escalation_threshold:
            return "ESCALATE", f"Fraud probability {fraud_probability:.2f} exceeds threshold of {settings.fraud_escalation_threshold}. Requires human review.", min(0.7, confidence)
        elif fraud_probability < 0.3:
            return "APPROVE", f"Clean claim. Fraud probability {fraud_probability:.2f} below threshold. Payout: ${calc['payout_amount']:.2f}", confidence
        else:
            return "ESCALATE", f"Ambiguous assessment. Fraud: {fraud_probability:.2f}. Escalating for human review.", min(0.6, confidence)

    async def run(self, state: dict) -> dict:
        claim = state.get("claim_payload", {})
        validation = state.get("validation_result", {})
        bundle = state.get("investigation_bundle", {})
        fraud = state.get("fraud_assessment", {})
        if not claim or not validation:
            raise AgentError("Missing claim or validation data for settlement", self.name, recoverable=False)

        self._log_reasoning(state, "Settlement Agent calculating final decision")

        calc = self._calculate_settlement(claim, validation, bundle, fraud)
        decision, reasoning, confidence = self._decide(claim, validation, fraud, calc)

        claimant_data = {
            "name": claim.get("claimant_name", "Valued Customer"),
            "address": claim.get("claimant_address", "On file"),
            "policy": claim.get("policy_number", "N/A"),
            "claim_number": claim.get("claim_number", "N/A"),
        }

        decision_details = {
            "decision": decision,
            **calc,
            "reasoning": reasoning,
            "fraud_risk": fraud.get("risk_tier", "UNKNOWN"),
        }

        letter_text = ""
        pdf_path = ""
        try:
            letter_text = generate_settlement_letter(decision, claimant_data, decision_details)
            self._log_tool_call(state, "generate_settlement_letter", f"{decision}|{claimant_data['name']}", "success")

            pdf_dir = os.path.join(os.path.dirname(__file__), "..", "data", "output_pdfs")
            os.makedirs(pdf_dir, exist_ok=True)
            pdf_path = os.path.join(pdf_dir, f"decision_{claim.get('claim_number', 'unknown')}.pdf")
            render_decision_pdf(letter_text, pdf_path)
            self._log_tool_call(state, "render_decision_pdf", pdf_path, "success")
        except Exception as e:
            self._log_tool_call(state, "generate_settlement_letter", "N/A", None, success=False, error=str(e))
            letter_text = f"Decision: {decision}\n\n{reasoning}\n\nAmount: ${calc['payout_amount']:.2f}"

        settlement_decision = {
            "decision": decision,
            **calc,
            "reasoning_chain": [
                {"step": "coverage_check", "result": validation.get("coverage_status"), "source": "ValidationAgent"},
                {"step": "fraud_assessment", "result": f"{fraud.get('risk_tier')} ({fraud.get('fraud_probability_score', 0):.2f})", "source": "FraudAgent"},
                {"step": "calculation", "result": f"Claim: ${calc['settlement_amount']:.2f}, Deductible: ${calc['deductible_applied']:.2f}, Payout: ${calc['payout_amount']:.2f}", "source": "SettlementAgent"},
                {"step": "decision", "result": decision, "reasoning": reasoning, "source": "SettlementAgent"},
            ],
            "decision_letter_text": letter_text,
            "confidence_score": confidence,
        }

        state["settlement_decision"] = settlement_decision
        self._log_reasoning(state, f"Settlement decision: {decision} (payout: ${calc['payout_amount']:.2f}, confidence: {confidence:.2f})")

        return state
