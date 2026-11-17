
from functools import partial

from langgraph.graph import StateGraph, START, END

from sentineledge.agent.state import AgentState
from sentineledge.agent.nodes import (
    validate_input,
    detect_injection,
    planner,
    llm_planner_node,
    safety_supervisor,
    execute_tool,
    direct_response,
    blocked_response,
)

from sentineledge.safety.permissions import ToolPermissionManager
from sentineledge.safety.injection_detector import PromptInjectionDetector
from sentineledge.safety.trust_boundary import TrustBoundaryFormatter

from sentineledge.tools.registry import ToolExecutor
from sentineledge.tools.calculator import CalculatorTool

from sentineledge.inference.mock_backend import MockInferenceBackend


def build_agent_graph(
    inference_backend=None,
    planner_backend=None,
):
    permission_manager = ToolPermissionManager()
    injection_detector = PromptInjectionDetector()
    trust_boundary = TrustBoundaryFormatter()

    backend = (
        inference_backend
        if inference_backend is not None
        else MockInferenceBackend()
    )

    executor = ToolExecutor(permission_manager)

    calculator = CalculatorTool()
    executor.register("calculator", calculator.calculate)

    workflow = StateGraph(AgentState)

    workflow.add_node("validate_input", validate_input)

    workflow.add_node(
        "detect_injection",
        partial(
            detect_injection,
            detector=injection_detector,
        ),
    )

    if planner_backend is None:
        workflow.add_node("planner", planner)
    else:
        workflow.add_node(
            "planner",
            partial(
                llm_planner_node,
                planner_instance=planner_backend,
            ),
        )

    workflow.add_node(
        "safety_supervisor",
        partial(
            safety_supervisor,
            permission_manager=permission_manager,
        ),
    )

    workflow.add_node(
        "execute_tool",
        partial(
            execute_tool,
            executor=executor,
        ),
    )

    workflow.add_node(
        "direct_response",
        partial(
            direct_response,
            backend=backend,
            formatter=trust_boundary,
        ),
    )

    workflow.add_node("blocked_response", blocked_response)

    workflow.add_edge(START, "validate_input")

    workflow.add_conditional_edges(
        "validate_input",
        lambda state: (
            "blocked_response"
            if state["decision"] != "allow"
            else "detect_injection"
        ),
    )

    workflow.add_conditional_edges(
        "detect_injection",
        lambda state: (
            "blocked_response"
            if state.get("injection_detected", False)
            else "planner"
        ),
    )

    workflow.add_edge("planner", "safety_supervisor")

    workflow.add_conditional_edges(
        "safety_supervisor",
        lambda state: (
            "blocked_response"
            if state["decision"] != "allow"
            else (
                "execute_tool"
                if state.get("tool_name") is not None
                else "direct_response"
            )
        ),
    )

    workflow.add_edge("execute_tool", END)
    workflow.add_edge("direct_response", END)
    workflow.add_edge("blocked_response", END)

    return workflow.compile()
