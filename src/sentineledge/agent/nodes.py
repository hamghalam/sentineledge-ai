
import re
from typing import Any

from sentineledge.safety.policy_engine import PolicyEngine
from sentineledge.safety.permissions import (
    ToolPermissionManager,
    AuthorizationDecision,
)
from sentineledge.safety.injection_detector import PromptInjectionDetector
from sentineledge.safety.trust_boundary import TrustBoundaryFormatter
from sentineledge.tools.registry import ToolExecutor
from sentineledge.inference.mock_backend import MockInferenceBackend

from sentineledge.agent.state import AgentState


def validate_input(state: AgentState) -> dict:

    text = state.get("user_input", "")

    if not text or not text.strip():
        return {
            "decision": "deny",
            "message": "Input cannot be empty.",
        }

    if len(text) > PolicyEngine.MAX_INPUT_LENGTH:
        return {
            "decision": "deny",
            "message": "Input exceeds the maximum allowed length.",
        }

    return {
        "decision": "allow",
        "message": "Input validation passed.",
    }


def detect_injection(
    state: AgentState,
    detector: PromptInjectionDetector,
) -> dict:

    result = detector.detect(state["user_input"])

    if result.is_suspicious:
        return {
            "injection_detected": True,
            "decision": "deny",
            "message": "Potential prompt injection detected.",
        }

    return {
        "injection_detected": False,
    }


def planner(state: AgentState) -> dict:
    """
    Baseline deterministic planner.

    Currently supports calculator selection.
    An LLM-based planner will replace this implementation later.
    """

    text = state["user_input"].strip()

    pattern = r"^\s*(?:calculate|compute|what\s+is)\s+(.+?)\s*\??\s*$"

    match = re.match(pattern, text, flags=re.IGNORECASE)

    if match:
        expression = match.group(1).strip().rstrip("?").strip()

        # Only select the calculator for arithmetic expressions.
        if re.fullmatch(r"[0-9\s()+\-*/.]+", expression):

            return {
                "tool_name": "calculator",
                "tool_args": {
                    "expression": expression,
                },
                "message": "Planner selected the calculator tool.",
            }

    return {
        "tool_name": None,
        "tool_args": {},
        "message": "Planner selected direct response.",
    }


def safety_supervisor(
    state: AgentState,
    permission_manager: ToolPermissionManager,
) -> dict:

    tool_name = state.get("tool_name")

    # No tool execution is required.
    if tool_name is None:
        return {
            "decision": "allow",
            "message": "No tool execution required.",
        }

    authorization = permission_manager.authorize(tool_name)

    if authorization.decision != AuthorizationDecision.ALLOW:
        return {
            "decision": authorization.decision.value,
            "message": authorization.reason,
        }

    return {
        "decision": "allow",
        "message": "Tool authorization passed.",
    }


def execute_tool(
    state: AgentState,
    executor: ToolExecutor,
) -> dict:

    try:
        execution = executor.execute(
            state["tool_name"],
            **state.get("tool_args", {}),
        )

        return {
            "decision": execution.decision,
            "message": execution.message,
            "result": execution.result,
        }

    except Exception:
        # Do not expose internal exception details to the caller.
        return {
            "decision": "error",
            "message": "Tool execution failed.",
            "result": None,
        }


def direct_response(
    state: AgentState,
    backend: MockInferenceBackend,
    formatter: TrustBoundaryFormatter,
) -> dict:

    safe_prompt = formatter.format(
        user_request=state["user_input"],
    )

    result = backend.generate(safe_prompt)

    return {
        "decision": "allow",
        "message": "Request processed without tool execution.",
        "result": result,
    }


def blocked_response(state: AgentState) -> dict:

    return {
        "result": None,
    }
