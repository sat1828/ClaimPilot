import json
import logging
import os
import uuid
from datetime import datetime
from typing import Optional, Any

import anthropic

from config import settings
from agents.base_agent import BaseAgent, AgentError
from tools.pdf_parser import parse_pdf
from orchestrator.state_schema import ClaimPayload

logger = logging.getLogger(__name__)

INTAKE_SYSTEM_PROMPT = """You are the Intake Agent for ClaimPilot, an autonomous insurance claims processing system.

Your role: Process incoming claim submissions in any modality (PDF, image, text, voice memo)
and extract structured claim data into a canonical ClaimPayload format.

You must NEVER guess or hallucinate data. If information is missing, ambiguous, or unclear, 
set the field to null and add it to the incomplete_fields list.

Available tools:
- parse_pdf(file_path): Extract text and images from a PDF document
- transcribe_audio(file_path): Transcribe a voice memo to text
- extract_images(claim_id): Extract embedded images from claim documents

Your output MUST be a valid JSON matching the ClaimPayload schema.
If critical fields (claimant_name, claim_type, policy_number, event_date) are missing,
set status to INCOMPLETE_SUBMISSION and include a clarification_required list.

Reason step by step before calling each tool. After calling all needed tools,
produce the structured output."""


INTAKE_TOOLS = [
    {
        "name": "parse_pdf",
        "description": "Extract structured text content and metadata from a PDF file. Returns text, tables, and images found in the document.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Absolute path to the PDF file"}
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "transcribe_audio",
        "description": "Transcribe an audio/voice memo file to text using Whisper API. Returns the full transcript.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Absolute path to the audio file"}
            },
            "required": ["file_path"]
        }
    },
]


class IntakeAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="intake_agent", max_retries=3)
        self._client = None

    @property
    def client(self):
        if self._client is None:
            api_key = settings.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY", "dummy-key")
            self._client = anthropic.Anthropic(api_key=api_key)
        return self._client

    def _parse_with_claude(self, raw_text: str) -> dict:
        messages = [
            {"role": "user", "content": f"Extract structured claim data from the following submission text. Return a valid JSON object matching the ClaimPayload schema:\n\n{raw_text}"}
        ]
        response = self.client.messages.create(
            model=settings.claude_model,
            max_tokens=4096,
            system=INTAKE_SYSTEM_PROMPT + "\n\nReturn only valid JSON matching the ClaimPayload schema.",
            messages=messages,
            temperature=0.1,
        )
        content = response.content[0].text
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            content = content[start:end]
        return json.loads(content)

    async def run(self, state: dict) -> dict:
        raw_input = state.get("raw_input", {})
        if not raw_input:
            raise AgentError("No raw input provided to Intake Agent", self.name, recoverable=False)

        self._log_reasoning(state, "Intake Agent started processing claim submission")

        claim_payload = {}

        input_type = raw_input.get("type", "text")
        content = raw_input.get("content", "")
        file_path = raw_input.get("file_path")

        if input_type == "pdf" and file_path and os.path.exists(file_path):
            self._log_reasoning(state, f"Processing PDF input: {file_path}")
            text = parse_pdf(file_path)
            claim_payload = self._parse_with_claude(text)
            claim_payload["raw_input_type"] = "pdf"
            claim_payload["raw_input_path"] = file_path
        elif input_type == "text":
            self._log_reasoning(state, "Processing direct text input")
            claim_payload = self._parse_with_claude(content)
            claim_payload["raw_input_type"] = "text"
        elif input_type == "audio" and file_path and os.path.exists(file_path):
            self._log_reasoning(state, f"Processing audio input: {file_path}")
            from tools.pdf_parser import transcribe_audio
            transcript = transcribe_audio(file_path)
            claim_payload = self._parse_with_claude(transcript)
            claim_payload["raw_input_type"] = "audio"
            claim_payload["raw_input_path"] = file_path
        else:
            claim_payload = self._parse_with_claude(str(content))

        claim_payload["claim_id"] = claim_payload.get("claim_id") or str(uuid.uuid4())
        claim_payload["claim_number"] = claim_payload.get("claim_number") or f"CP-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        claim_payload["submission_date"] = claim_payload.get("submission_date") or datetime.utcnow().isoformat()

        state["claim_payload"] = claim_payload

        self._log_reasoning(state, f"Intake complete. Claim {claim_payload.get('claim_number')} created. Type: {claim_payload.get('claim_type', 'unknown')}")

        return state
