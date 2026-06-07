import pytest
import os
import sys
from unittest.mock import patch, AsyncMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

_HAS_ANTHROPIC = bool(os.getenv("ANTHROPIC_API_KEY"))


class TestIntakeAgent:
    @pytest.mark.asyncio
    @pytest.mark.skipif(not _HAS_ANTHROPIC, reason="Requires ANTHROPIC_API_KEY")
    async def test_intake_text_input(self, sample_state):
        from agents.intake_agent import IntakeAgent
        agent = IntakeAgent()
        state = await agent.run(sample_state)
        assert "claim_payload" in state
        payload = state["claim_payload"]
        assert payload.get("claim_type") is not None

    @pytest.mark.asyncio
    async def test_intake_empty_input(self):
        from agents.intake_agent import IntakeAgent
        agent = IntakeAgent()
        with pytest.raises(Exception):
            await agent.run({"raw_input": {}})


class TestValidationAgent:
    @pytest.mark.asyncio
    @pytest.mark.skipif(not _HAS_ANTHROPIC, reason="Requires ANTHROPIC_API_KEY")
    async def test_validation_valid_claim(self, sample_state):
        from agents.validation_agent import ValidationAgent
        agent = ValidationAgent()
        state = await agent.run(sample_state)
        assert "validation_result" in state
        result = state["validation_result"]
        assert "coverage_status" in result

    @pytest.mark.asyncio
    async def test_validation_no_payload(self):
        from agents.validation_agent import ValidationAgent
        agent = ValidationAgent()
        with pytest.raises(Exception):
            await agent.run({})


class TestInvestigationAgent:
    @pytest.mark.asyncio
    async def test_investigation_auto_claim(self, sample_state):
        from agents.investigation_agent import InvestigationAgent
        agent = InvestigationAgent()
        state = await agent.run(sample_state)
        assert "investigation_bundle" in state
        bundle = state["investigation_bundle"]
        assert "evidence_items" in bundle
        assert "evidence_gaps" in bundle
        assert "investigation_summary" in bundle

    @pytest.mark.asyncio
    async def test_investigation_no_payload(self):
        from agents.investigation_agent import InvestigationAgent
        with pytest.raises(Exception):
            await InvestigationAgent().run({})


class TestFraudAgent:
    @pytest.mark.asyncio
    async def test_fraud_detection(self, sample_state):
        from agents.fraud_agent import FraudAgent
        sample_state["investigation_bundle"] = {
            "evidence_items": [],
            "evidence_gaps": [],
            "investigation_summary": "Test investigation",
            "confidence_score": 0.8,
        }
        sample_state["validation_result"] = {
            "coverage_status": "COVERED",
            "confidence_score": 0.9,
        }
        agent = FraudAgent()
        state = await agent.run(sample_state)
        assert "fraud_assessment" in state
        assessment = state["fraud_assessment"]
        assert "fraud_probability_score" in assessment
        assert "risk_tier" in assessment
        assert 0.0 <= assessment["fraud_probability_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_fraud_empty_state(self, sample_state):
        from agents.fraud_agent import FraudAgent
        with pytest.raises(Exception):
            await FraudAgent().run({})


class TestSettlementAgent:
    @pytest.mark.asyncio
    async def test_settlement_approve(self, sample_state):
        from agents.settlement_agent import SettlementAgent
        sample_state["validation_result"] = {
            "coverage_status": "COVERED",
            "deductible": 1000,
            "policy_limits": {"coverage_limit": 100000},
            "confidence_score": 0.9,
        }
        sample_state["investigation_bundle"] = {
            "evidence_items": [],
            "evidence_gaps": [],
            "investigation_summary": "Test",
            "confidence_score": 0.8,
        }
        sample_state["fraud_assessment"] = {
            "fraud_probability_score": 0.05,
            "risk_tier": "LOW",
            "confidence_score": 0.95,
        }
        agent = SettlementAgent()
        state = await agent.run(sample_state)
        assert "settlement_decision" in state
        sd = state["settlement_decision"]
        assert "decision" in sd
        assert sd["decision"] in ("APPROVE", "REJECT", "ESCALATE")

    @pytest.mark.asyncio
    async def test_settlement_reject(self, sample_state):
        from agents.settlement_agent import SettlementAgent
        sample_state["validation_result"] = {
            "coverage_status": "NOT_COVERED",
            "deductible": 2500,
            "policy_limits": {},
            "confidence_score": 0.9,
        }
        sample_state["investigation_bundle"] = {
            "evidence_items": [],
            "evidence_gaps": ["No evidence available"],
            "investigation_summary": "Test",
            "confidence_score": 0.5,
        }
        sample_state["fraud_assessment"] = {
            "fraud_probability_score": 0.1,
            "risk_tier": "LOW",
            "confidence_score": 0.9,
        }
        agent = SettlementAgent()
        state = await agent.run(sample_state)
        assert state["settlement_decision"]["decision"] == "REJECT"


class TestHumanLoopAgent:
    @pytest.mark.asyncio
    async def test_human_loop_escalation(self, sample_state):
        from agents.human_loop_agent import HumanLoopAgent
        sample_state["settlement_decision"] = {
            "decision": "ESCALATE",
            "payout_amount": 0,
            "confidence_score": 0.4,
            "reasoning_chain": [],
        }
        agent = HumanLoopAgent()
        state = await agent.run(sample_state)
        assert "_human_case_summary" in state
        summary = state["_human_case_summary"]
        assert "claim_number" in summary
        assert "ai_recommended_action" in summary
