import logging
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


class AgentError(Exception):
    def __init__(self, message: str, agent: str, recoverable: bool = True):
        self.message = message
        self.agent = agent
        self.recoverable = recoverable
        super().__init__(self.message)


class BaseAgent:
    def __init__(self, name: str, max_retries: int = 3):
        self.name = name
        self.max_retries = max_retries

    def _log_tool_call(self, state: dict, tool_name: str, input_data: Any, output: Any, success: bool = True, error: Optional[str] = None) -> dict:
        chain = list(state.get("reasoning_chain", []))
        chain.append({
            "agent": self.name,
            "action": f"tool_call: {tool_name}",
            "input": str(input_data)[:500],
            "output": str(output)[:500] if success else None,
            "success": success,
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
        })
        state["reasoning_chain"] = chain
        return state

    def _log_reasoning(self, state: dict, reasoning: str) -> dict:
        chain = list(state.get("reasoning_chain", []))
        chain.append({
            "agent": self.name,
            "action": "reasoning",
            "reasoning": reasoning,
            "timestamp": datetime.utcnow().isoformat(),
        })
        state["reasoning_chain"] = chain
        return state

    def _update_retry_count(self, state: dict, agent_name: str) -> dict:
        retries = dict(state.get("retry_count", {}))
        retries[agent_name] = retries.get(agent_name, 0) + 1
        state["retry_count"] = retries
        return state

    def _should_escalate(self, state: dict) -> bool:
        retries = dict(state.get("retry_count", {}))
        return retries.get(self.name, 0) >= self.max_retries

    async def run(self, state: dict) -> dict:
        raise NotImplementedError("Each agent must implement run()")
