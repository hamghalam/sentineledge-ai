
import re

from sentineledge.safety.policy_engine import PolicyEngine
from sentineledge.safety.permissions import (
    ToolPermissionManager,
    AuthorizationDecision,
)
from sentineledge.safety.injection_detector import PromptInjectionDetector
from sentineledge.safety.trust_boundary import TrustBoundaryFormatter
from sentineledge.tools.registry import ToolExecutor
from sentineledge.inference.base import InferenceBackend

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
    """

    text = state["user_input"].strip()

    pattern = r"^\s*(?:calculate|compute|what\s+is)\s+(.+?)\s*\??\s*$"
    match = re.match(pattern, text, flags=re.IGNORECASE)

    if match:
        expression = match.group(1).strip().rstrip("?").strip()

        if re.fullmatch(r"[0-9\s()+\-*/.]+", expression):
            return {
                "planner_action": "tool_call",
                "tool_name": "calculator",
                "tool_args": {
                    "expression": expression,
                },
                "message": "Deterministic planner selected calculator.",
            }

    return {
        "planner_action": "direct_response",
        "tool_name": None,
        "tool_args": {},
        "message": "Deterministic planner selected direct response.",
    }


def llm_planner_node(
    state: AgentState,
    planner_instance,
) -> dict:
    """
    Run the LLM planner and convert its validated proposal
    into LangGraph state.

    The planner proposes actions but does not authorize execution.
    """

    try:
        proposal = planner_instance.plan(state["user_input"])

        return {
            "decision": "allow",
            "planner_action": proposal.action.value,
            "tool_name": proposal.tool_name,
            "tool_args": proposal.tool_args.model_dump(),
            "message": "LLM planner produced a validated proposal.",
        }

    except Exception:
        # Fail closed: a planner failure must never authorize execution.
        return {
            "decision": "deny",
            "planner_action": None,
            "tool_name": None,
            "tool_args": {},
            "message": "LLM planner failed. Request blocked.",
        }


def safety_supervisor(
    state: AgentState,
    permission_manager: ToolPermissionManager,
) -> dict:
    # Preserve any earlier denial or error.
    if state.get("decision") != "allow":
        return {
            "decision": state.get("decision", "deny"),
            "message": state.get(
                "message",
                "Request was blocked before authorization.",
            ),
        }

    tool_name = state.get("tool_name")

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
        return {
            "decision": "error",
            "message": "Tool execution failed.",
            "result": None,
        }


def direct_response(
    state: AgentState,
    backend: InferenceBackend,
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
