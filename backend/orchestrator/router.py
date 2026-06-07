def route_after_validation(state: dict) -> str:
    result = state.get("validation_result", {})
    coverage = result.get("coverage_status", "NOT_COVERED")
    if coverage == "COVERED":
        return "investigation"
    return "settlement"


def route_after_settlement(state: dict) -> str:
    decision = state.get("settlement_decision", {})
    verdict = decision.get("decision", "ESCALATE")
    if verdict == "APPROVE" or verdict == "REJECT":
        return "finalize"
    return "human_loop"


def route_human_loop(state: dict) -> str:
    decision = state.get("settlement_decision", {})
    verdict = decision.get("decision", "ESCALATE")
    if verdict == "ESCALATE":
        return "human_loop"
    return "finalize"
