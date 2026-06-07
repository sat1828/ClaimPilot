import json
import logging
import os
from typing import Optional

import anthropic

from config import settings
from agents.base_agent import BaseAgent, AgentError
from tools.email_client import push_to_dashboard
from orchestrator.state_schema import SettlementDecision

logger = logging.getLogger(__name__)

HUMAN_LOOP_SYSTEM_PROMPT = """You are the Human-in-the-Loop Agent for ClaimPilot.

Your role: When the Settlement Agent escalates a claim (ESCALATE verdict), you compile
a comprehensive case summary package for a human adjuster. This package includes:

1. One-page executive summary of the claim
2. Evidence links from the Investigation Agent  
3. Fraud risk summary with flagged anomalies
4. AI's recommended action with confidence score
5. Policy coverage interpretation with relevant sections highlighted

You then push this case to the adjuster dashboard via WebSocket.
When the human adjuster responds (APPROVE / REJECT / REQUEST_MORE_INFO),
you record their decision, log their reasoning, update the database,
and update the claim state accordingly.

If the human requests more info, you generate a list of specific 
clarification requests and route back for additional investigation."""

HUMAN_LOOP_TOOLS = [
    {
        "name": "push_to_dashboard",
        "description": "Push the case summary to the adjuster dashboard via WebSocket. The adjuster will see the summary and can make a decision.",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_summary": {"type": "object", "description": "The complete case summary for human review"},
                "adjuster_id": {"type": "string", "description": "Target adjuster identifier"}
            },
            "required": ["case_summary"]
        }
    },
    {
        "name": "record_human_decision",
        "description": "Record the human adjuster's final decision, reasoning, and any overrides to the AI recommendation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "claim_id": {"type": "string", "description": "Claim identifier"},
                "decision": {"type": "string", "description": "Human decision: APPROVE, REJECT, or REQUEST_MORE_INFO"},
                "adjuster_notes": {"type": "string", "description": "Adjuster's notes and reasoning"}
            },
            "required": ["claim_id", "decision"]
        }
    },
]


class HumanLoopAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="human_loop_agent", max_retries=3)
        self._client = None

    @property
    def client(self):
        if self._client is None:
            api_key = settings.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY", "dummy-key")
            self._client = anthropic.Anthropic(api_key=api_key)
        return self._client

    async def _build_case_summary(self, state: dict) -> dict:
        claim = state.get("claim_payload", {})
        validation = state.get("validation_result", {})
        bundle = state.get("investigation_bundle", {})
        fraud = state.get("fraud_assessment", {})
        settlement = state.get("settlement_decision", {})

        return {
            "claim_number": claim.get("claim_number", "N/A"),
            "claimant_name": claim.get("claimant_name", "N/A"),
            "claim_type": claim.get("claim_type", "N/A"),
            "event_date": claim.get("event_date", "N/A"),
            "submission_date": claim.get("submission_date", "N/A"),
            "incident_location": claim.get("incident_location", "N/A"),
            "claim_amount": claim.get("claim_amount", 0),
            "coverage_status": validation.get("coverage_status", "UNKNOWN"),
            "coverage_type": validation.get("coverage_type", "N/A"),
            "policy_exclusions": validation.get("policy_exclusions", []),
            "fraud_probability": fraud.get("fraud_probability_score", 0),
            "fraud_risk_tier": fraud.get("risk_tier", "UNKNOWN"),
            "fraud_flags": fraud.get("cited_flags", []),
            "evidence_count": len(bundle.get("evidence_items", [])),
            "evidence_gaps": bundle.get("evidence_gaps", []),
            "investigation_summary": bundle.get("investigation_summary", "No investigation data"),
            "ai_recommended_action": settlement.get("decision", "ESCALATE"),
            "ai_calculated_payout": settlement.get("payout_amount", 0),
            "ai_confidence_score": settlement.get("confidence_score", 0),
            "reasoning_chain": state.get("reasoning_chain", []),
            "status": "HUMAN_REVIEW",
        }

    async def run(self, state: dict) -> dict:
        claim = state.get("claim_payload", {})
        if not claim:
            raise AgentError("No claim payload for human-in-the-loop", self.name, recoverable=False)

        self._log_reasoning(state, "Human-in-the-Loop Agent compiling case for adjuster review")

        case_summary = await self._build_case_summary(state)

        state["_human_case_summary"] = case_summary

        try:
            adjuster_id = "default-adjuster"
            push_to_dashboard(case_summary, adjuster_id)
            self._log_tool_call(state, "push_to_dashboard",
                                f"Claim {claim.get('claim_number')} to {adjuster_id}", "Case pushed to dashboard")
        except Exception as e:
            self._log_tool_call(state, "push_to_dashboard", "N/A", None, success=False, error=str(e))

        from tools.email_client import record_human_decision

        messages = [
            {"role": "user", "content": f"""The following claim has been escalated for human review. Generate a comprehensive one-page executive summary.

Claim: {json.dumps(case_summary, indent=2, default=str)}

Format the summary for an adjuster dashboard. Include:
1. EXECUTIVE SUMMARY (3-4 bullet points)
2. WHY THIS WAS ESCALATED
3. KEY EVIDENCE
4. FRAUD CONCERNS
5. AI RECOMMENDATION
6. WHAT THE ADJUSTER NEEDS TO DECIDE

The summary should be professional and actionable."""}
        ]

        try:
            response = self.client.messages.create(
                model=settings.claude_model,
                max_tokens=2048,
                system=HUMAN_LOOP_SYSTEM_PROMPT,
                messages=messages,
                temperature=0.3,
            )
            summary_text = response.content[0].text
        except Exception as e:
            summary_text = f"Case #{claim.get('claim_number', 'N/A')} escalated. Adjuster review required."

        case_summary["executive_summary"] = summary_text
        case_summary["needs_human_decision"] = True
        state["_human_case_summary"] = case_summary

        self._log_reasoning(state, f"Human review requested for claim {claim.get('claim_number')}")

        settlement = dict(state.get("settlement_decision", {}))
        settlement["decision"] = "ESCALATE"
        settlement["confidence_score"] = min(
            settlement.get("confidence_score", 0.5),
            0.5
        )
        settlement["reasoning_chain"] = settlement.get("reasoning_chain", []) + [
            {"step": "human_escalation", "result": "Escalated to human adjuster", "source": "HumanLoopAgent"}
        ]
        state["settlement_decision"] = settlement

        return state
