import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

from langgraph.graph import StateGraph, END

try:
    from langgraph.checkpoint.postgres import PostgresSaver
    CHECKPOINTER_AVAILABLE = True
except ImportError:
    PostgresSaver = None
    CHECKPOINTER_AVAILABLE = False

from .state_schema import ClaimState
from .router import route_after_validation, route_after_settlement
from agents.intake_agent import IntakeAgent
from agents.validation_agent import ValidationAgent
from agents.investigation_agent import InvestigationAgent
from agents.fraud_agent import FraudAgent
from agents.settlement_agent import SettlementAgent
from agents.human_loop_agent import HumanLoopAgent

logger = logging.getLogger(__name__)

CHECKPOINT_URI = "postgresql://claimpilot:claimpilot@postgres:5432/claimpilot"


class ClaimPipeline:
    def __init__(self):
        self.intake_agent = IntakeAgent()
        self.validation_agent = ValidationAgent()
        self.investigation_agent = InvestigationAgent()
        self.fraud_agent = FraudAgent()
        self.settlement_agent = SettlementAgent()
        self.human_loop_agent = HumanLoopAgent()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        builder = StateGraph(ClaimState)

        builder.add_node("intake", self._run_intake)
        builder.add_node("validation", self._run_validation)
        builder.add_node("investigation", self._run_investigation)
        builder.add_node("fraud_detection", self._run_fraud)
        builder.add_node("settlement", self._run_settlement)
        builder.add_node("human_loop", self._run_human_loop)
        builder.add_node("finalize", self._run_finalize)

        builder.set_entry_point("intake")
        builder.add_edge("intake", "validation")
        builder.add_conditional_edges(
            "validation",
            route_after_validation,
            {"investigation": "investigation", "settlement": "settlement"}
        )
        builder.add_edge("investigation", "fraud_detection")
        builder.add_conditional_edges(
            "fraud_detection",
            lambda s: "settlement",
            {"settlement": "settlement"}
        )
        builder.add_conditional_edges(
            "settlement",
            route_after_settlement,
            {"finalize": "finalize", "human_loop": "human_loop"}
        )
        builder.add_conditional_edges(
            "human_loop",
            lambda s: route_after_settlement(s),
            {"finalize": "finalize", "human_loop": "human_loop"}
        )
        builder.add_edge("finalize", END)

        if CHECKPOINTER_AVAILABLE and PostgresSaver is not None:
            checkpointer = PostgresSaver.from_conn_string(CHECKPOINT_URI)
            logger.info("Using PostgresSaver checkpointer")
        else:
            checkpointer = None
            logger.info("Running without checkpointing (install langgraph-checkpoint-postgres for persistence)")

        return builder.compile(checkpointer=checkpointer)

    def _append_reasoning(self, state: dict, entry: dict) -> dict:
        chain = list(state.get("reasoning_chain", []))
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        chain.append(entry)
        state["reasoning_chain"] = chain
        return state

    async def _run_intake(self, state: ClaimState) -> ClaimState:
        logger.info(f"[Pipeline] Running Intake Agent for claim {state.get('claim_id')}")
        state["current_agent"] = "intake"
        result = await self.intake_agent.run(state)
        state.update(result)
        state["current_status"] = "INTAKE_COMPLETE"
        state = self._append_reasoning(state, {
            "agent": "intake", "action": "intake_complete",
            "claim_payload": state.get("claim_payload"),
            "confidence": state.get("claim_payload", {}).get("claim_id", "N/A"),
        })
        return state

    async def _run_validation(self, state: ClaimState) -> ClaimState:
        logger.info(f"[Pipeline] Running Validation Agent for claim {state.get('claim_id')}")
        state["current_agent"] = "validation"
        result = await self.validation_agent.run(state)
        state.update(result)
        validation = state.get("validation_result", {})
        if validation.get("coverage_status") == "COVERED":
            state["current_status"] = "VALIDATION_PASSED"
        else:
            state["current_status"] = "VALIDATION_FAILED"
        state = self._append_reasoning(state, {
            "agent": "validation", "action": "validation_complete",
            "result": validation,
            "confidence": validation.get("confidence_score"),
        })
        return state

    async def _run_investigation(self, state: ClaimState) -> ClaimState:
        logger.info(f"[Pipeline] Running Investigation Agent for claim {state.get('claim_id')}")
        state["current_agent"] = "investigation"
        result = await self.investigation_agent.run(state)
        state.update(result)
        state["current_status"] = "INVESTIGATION_COMPLETE"
        bundle = state.get("investigation_bundle", {})
        state = self._append_reasoning(state, {
            "agent": "investigation", "action": "investigation_complete",
            "evidence_count": len(bundle.get("evidence_items", [])),
            "gaps": bundle.get("evidence_gaps", []),
            "confidence": bundle.get("confidence_score"),
        })
        return state

    async def _run_fraud(self, state: ClaimState) -> ClaimState:
        logger.info(f"[Pipeline] Running Fraud Detection Agent for claim {state.get('claim_id')}")
        state["current_agent"] = "fraud_detection"
        result = await self.fraud_agent.run(state)
        state.update(result)
        state["current_status"] = "FRAUD_ASSESSMENT_COMPLETE"
        assessment = state.get("fraud_assessment", {})
        state = self._append_reasoning(state, {
            "agent": "fraud_detection", "action": "fraud_assessment_complete",
            "fraud_probability": assessment.get("fraud_probability_score"),
            "risk_tier": assessment.get("risk_tier"),
            "confidence": assessment.get("confidence_score"),
        })
        return state

    async def _run_settlement(self, state: ClaimState) -> ClaimState:
        logger.info(f"[Pipeline] Running Settlement Agent for claim {state.get('claim_id')}")
        state["current_agent"] = "settlement"
        result = await self.settlement_agent.run(state)
        state.update(result)
        decision = state.get("settlement_decision", {})
        state["current_status"] = decision.get("decision", "ESCALATED")
        state = self._append_reasoning(state, {
            "agent": "settlement", "action": "settlement_complete",
            "decision": decision.get("decision"),
            "payout": decision.get("payout_amount"),
            "confidence": decision.get("confidence_score"),
        })
        return state

    async def _run_human_loop(self, state: ClaimState) -> ClaimState:
        logger.info(f"[Pipeline] Running Human-in-Loop Agent for claim {state.get('claim_id')}")
        state["current_agent"] = "human_loop"
        state["current_status"] = "HUMAN_REVIEW"
        result = await self.human_loop_agent.run(state)
        state.update(result)
        decision = state.get("settlement_decision", {})
        state["current_status"] = decision.get("decision", "ESCALATED")
        state = self._append_reasoning(state, {
            "agent": "human_loop", "action": "human_review_complete",
            "human_decision": decision.get("decision"),
            "confidence": decision.get("confidence_score"),
        })
        return state

    async def _run_finalize(self, state: ClaimState) -> ClaimState:
        logger.info(f"[Pipeline] Finalizing claim {state.get('claim_id')}")
        state["current_agent"] = "finalize"
        state["pipeline_completed_at"] = datetime.now(timezone.utc).isoformat()
        state["current_status"] = "CLOSED"
        state = self._append_reasoning(state, {
            "agent": "finalize", "action": "pipeline_complete",
            "final_status": "CLOSED",
        })
        return state

    async def run(self, initial_state: dict) -> dict:
        initial_state["pipeline_started_at"] = datetime.now(timezone.utc).isoformat()
        config = {"configurable": {"thread_id": initial_state.get("claim_id", "default")}}
        result = await self.graph.ainvoke(initial_state, config)
        return result


pipeline = ClaimPipeline()
