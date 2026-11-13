import pytest

from sentineledge.safety.permissions import (
    ToolPermissionManager,
    AuthorizationDecision,
)

from sentineledge.tools.registry import ToolExecutor
from sentineledge.tools.calculator import CalculatorTool


def test_read_only_tool_is_allowed():
    manager = ToolPermissionManager()

    result = manager.authorize("calculator")

    assert result.decision == AuthorizationDecision.ALLOW


def test_sensitive_tool_requires_approval():
    manager = ToolPermissionManager()

    result = manager.authorize("send_email")

    assert result.decision == AuthorizationDecision.REQUIRE_APPROVAL


def test_unknown_tool_is_denied():
    manager = ToolPermissionManager()

    result = manager.authorize("execute_shell")

    assert result.decision == AuthorizationDecision.DENY


def test_sensitive_tool_cannot_execute():
    manager = ToolPermissionManager()
    executor = ToolExecutor(manager)

    execution_log = []

    def fake_send_email(recipient, message):
        execution_log.append(recipient)
        return "Email sent"

    executor.register("send_email", fake_send_email)

    result = executor.execute(
        "send_email",
        recipient="test@example.com",
        message="Hello",
    )

    assert result.decision == "require_approval"
    assert execution_log == []


def test_calculator_executes_successfully():
    manager = ToolPermissionManager()
    executor = ToolExecutor(manager)
    calculator = CalculatorTool()

    executor.register("calculator", calculator.calculate)

    result = executor.execute(
        "calculator",
        expression="(10 + 5) * 2",
    )

    assert result.decision == "allow"
    assert result.result == 30


def test_unknown_tool_cannot_be_registered():
    manager = ToolPermissionManager()
    executor = ToolExecutor(manager)

    with pytest.raises(ValueError):
        executor.register("execute_shell", lambda: "executed")


def test_calculator_rejects_python_code():
    calculator = CalculatorTool()

    with pytest.raises((ValueError, SyntaxError)):
        calculator.calculate("__import__('os').system('whoami')")


def test_calculator_rejects_unsupported_operator():
    calculator = CalculatorTool()

    with pytest.raises(ValueError):
        calculator.calculate("2 // 1")