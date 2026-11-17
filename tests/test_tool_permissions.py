import pytest

from sentineledge.safety.permissions import (
    ToolPermissionManager,
    AuthorizationDecision,
)

from sentineledge.tools.registry import ToolExecutor
from sentineledge.tools.calculator import CalculatorTool


from sentineledge.safety.permissions import ToolPermissionManager
from sentineledge.tools.registry import ToolExecutor



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
        
        




def test_executor_rejects_duplicate_registration():
    executor = ToolExecutor(ToolPermissionManager())

    def calculator(expression: str):
        return 10

    executor.register("calculator", calculator)

    with pytest.raises(ValueError, match="already registered"):
        executor.register("calculator", calculator)


def test_executor_rejects_non_callable_registration():
    executor = ToolExecutor(ToolPermissionManager())

    with pytest.raises(TypeError, match="must be callable"):
        executor.register("calculator", "not-a-function")


def test_executor_validates_arguments_before_execution():
    executor = ToolExecutor(ToolPermissionManager())

    execution_tracker = {"called": False}

    def calculator(expression: str):
        execution_tracker["called"] = True
        return 10

    executor.register("calculator", calculator)

    with pytest.raises(TypeError, match="Invalid arguments"):
        executor.execute("calculator", wrong_argument=10)

    assert execution_tracker["called"] is False
    
def test_executor_rejects_wrong_argument_type():
    executor = ToolExecutor(ToolPermissionManager())
    execution_tracker = {"called": False}

    def calculator(expression):
        execution_tracker["called"] = True
        return 10

    executor.register("calculator", calculator)

    result = executor.execute(
        "calculator",
        expression=125,
    )

    assert result.decision == "deny"
    assert execution_tracker["called"] is False


def test_executor_rejects_empty_expression():
    executor = ToolExecutor(ToolPermissionManager())
    execution_tracker = {"called": False}

    def calculator(expression):
        execution_tracker["called"] = True
        return 10

    executor.register("calculator", calculator)

    result = executor.execute(
        "calculator",
        expression="   ",
    )

    assert result.decision == "deny"
    assert execution_tracker["called"] is False


def test_executor_rejects_expression_longer_than_100_characters():
    executor = ToolExecutor(ToolPermissionManager())
    execution_tracker = {"called": False}

    def calculator(expression):
        execution_tracker["called"] = True
        return 10

    executor.register("calculator", calculator)

    result = executor.execute(
        "calculator",
        expression="1" * 101,
    )

    assert result.decision == "deny"
    assert execution_tracker["called"] is False


def test_executor_rejects_extra_arguments_before_execution():
    executor = ToolExecutor(ToolPermissionManager())
    execution_tracker = {"called": False}

    def calculator(expression):
        execution_tracker["called"] = True
        return 10

    executor.register("calculator", calculator)

    with pytest.raises(TypeError, match="Invalid arguments"):
        executor.execute(
            "calculator",
            expression="125 * 8",
            value=125,
        )

    assert execution_tracker["called"] is False
        