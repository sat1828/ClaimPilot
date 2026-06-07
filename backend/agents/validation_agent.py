import json
import logging
from datetime import datetime, date
from typing import Optional

import anthropic

from config import settings
from agents.base_agent import BaseAgent, AgentError
from tools.vector_store import retrieve_policy_chunks, get_policy_metadata
from orchestrator.state_schema import ValidationResult

logger = logging.getLogger(__name__)

VALIDATION_SYSTEM_PROMPT = """You are the Validation Agent for ClaimPilot. You are the gatekeeper.

Your role: Determine whether a claim is eligible for processing by analyzing:
1. Is this event type covered under the claimant's policy?
2. Is the claimant within the active policy period?
3. Are all mandatory fields present in the claim?

You use RAG to retrieve relevant policy sections from a vector database, then reason over them.

Available tools:
- retrieve_policy_chunks(policy_number, query): Retrieves relevant chunks from the policy document
- check_policy_dates(policy_id, event_date): Validates the event date falls within policy coverage period

Output a structured ValidationResult with:
- coverage_status: "COVERED", "NOT_COVERED", or "PARTIALLY_COVERED"
- policy_period_valid: boolean
- missing_fields: list of missing required fields
- coverage_type: specific coverage provision that applies
- policy_exclusions: list of applicable exclusions found
- reasoning: your chain of thought for this decision
- confidence_score: 0.0 to 1.0

If confidence_score < 0.6, note low confidence in reasoning chain.
If confidence_score < 0.4, the system will auto-escalate.

Be thorough. Policy language is precise. Cite specific policy sections in your reasoning."""

VALIDATION_TOOLS = [
    {
        "name": "retrieve_policy_chunks",
        "description": "Search the policy document for relevant sections using hybrid search (semantic + keyword). Returns the most relevant chunks with their source locations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "policy_number": {"type": "string", "description": "The claimant's policy number"},
                "query": {"type": "string", "description": "The search query to find relevant policy sections"}
            },
            "required": ["policy_number", "query"]
        }
    },
    {
        "name": "check_policy_dates",
        "description": "Check whether the claim event date falls within the policy's active coverage period.",
        "input_schema": {
            "type": "object",
            "properties": {
                "policy_number": {"type": "string", "description": "The claimant's policy number"},
                "event_date": {"type": "string", "description": "The date of the claimed event (ISO format)"}
            },
            "required": ["policy_number", "event_date"]
        }
    },
]


class ValidationAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="validation_agent", max_retries=3)
        self._client = None

    @property
    def client(self):
        if self._client is None:
            api_key = settings.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY", "dummy-key")
            self._client = anthropic.Anthropic(api_key=api_key)
        return self._client

    async def run(self, state: dict) -> dict:
        claim = state.get("claim_payload", {})
        if not claim:
            raise AgentError("No claim_payload in state for validation", self.name, recoverable=False)

        self._log_reasoning(state, f"Validation Agent reviewing claim {claim.get('claim_number')}")

        policy_number = claim.get("policy_number", "")
        event_description = claim.get("event_description", "")
        claim_type = claim.get("claim_type", "")
        event_date = claim.get("event_date", "")

        coverage_queries = [
            f"Coverage for {claim_type} claims - {event_description[:200]}",
            f"Does this policy cover {claim_type} events?",
            f"Policy exclusions for {claim_type}",
        ]

        all_chunks = []
        for query in coverage_queries:
            chunks = retrieve_policy_chunks(policy_number, query, top_k=5)
            all_chunks.extend(chunks)

        self._log_tool_call(state, "retrieve_policy_chunks",
                            {"policy": policy_number}, f"Retrieved {len(all_chunks)} chunks")

        policy_text = "\n\n---\n\n".join([c.get("text", "") for c in all_chunks])

        messages = [
            {"role": "user", "content": f"""Analyze this claim against the policy document.

Claim Information:
- Claim Type: {claim_type}
- Event Date: {event_date}
- Event Description: {event_description[:500]}
- Claim Amount: {claim.get('claim_amount', 'N/A')}
- Policy Number: {policy_number}

Relevant Policy Sections:
{policy_text[:12000]}

Determine:
1. Is this event type covered by this policy?
2. Is the event within the active policy period?
3. Are any mandatory fields missing from the claim?
4. What specific coverage type or exclusion applies?
5. What is your confidence in this assessment?

Return a JSON object with the ValidationResult schema fields."""}
        ]

        response = self.client.messages.create(
            model=settings.claude_model,
            max_tokens=4096,
            system=VALIDATION_SYSTEM_PROMPT,
            messages=messages,
            temperature=0.1,
        )

        content = response.content[0].text
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            content = content[start:end]

        try:
            result = json.loads(content)
        except json.JSONDecodeError as e:
            self._log_reasoning(state, f"Failed to parse Claude response as JSON: {e}")
            result = {
                "coverage_status": "NOT_COVERED",
                "policy_period_valid": False,
                "missing_fields": ["_parse_error"],
                "reasoning": "Failed to parse validation response",
                "confidence_score": 0.0,
            }

        required_fields = ["claimant_name", "policy_number", "event_date", "claim_type", "event_description"]
        missing = [f for f in required_fields if not claim.get(f)]
        result["missing_fields"] = result.get("missing_fields", []) + missing

        state["validation_result"] = result

        self._log_reasoning(state, f"Validation result: {result.get('coverage_status')} (confidence: {result.get('confidence_score', 'N/A')})")

        return state
