
from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    user_input: str

    # Planner output
    tool_name: str | None
    tool_args: dict[str, Any]

    # Safety and execution status
    decision: str
    message: str
    injection_detected: bool

    # Final result
    result: Any

