
from dataclasses import dataclass
from inspect import signature
from typing import Any, Callable

from sentineledge.safety.permissions import (
    ToolPermissionManager,
    AuthorizationDecision,
)


@dataclass
class ToolExecutionResult:
    decision: str
    message: str
    result: Any = None


class ToolExecutor:
    def __init__(self, permission_manager: ToolPermissionManager):
        self.permission_manager = permission_manager
        self.tools: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, function: Callable[..., Any]):
        # Only tools defined in the permission policy can be registered.
        if name not in self.permission_manager.TOOL_PERMISSIONS:
            raise ValueError(
                f"Tool '{name}' is not in the permission policy."
            )

        # Reject non-callable objects.
        if not callable(function):
            raise TypeError("Registered tool must be callable.")

        # Prevent accidental replacement of an existing tool.
        if name in self.tools:
            raise ValueError(f"Tool '{name}' is already registered.")

        self.tools[name] = function

    def execute(self, name: str, **kwargs) -> ToolExecutionResult:

        # 1. Check authorization before looking up or executing the tool.
        authorization = self.permission_manager.authorize(name)

        if authorization.decision != AuthorizationDecision.ALLOW:
            return ToolExecutionResult(
                decision=authorization.decision.value,
                message=authorization.reason,
            )

        # 2. Verify that the tool has an implementation.
        function = self.tools.get(name)

        if function is None:
            return ToolExecutionResult(
                decision="deny",
                message="Tool is registered in policy but has no implementation.",
            )

        # 3. Validate arguments before execution.
        try:
            signature(function).bind(**kwargs)
        except TypeError as exc:
            raise TypeError(
                f"Invalid arguments for tool '{name}'."
            ) from exc

        # 4. Execute only after authorization and validation.
        result = function(**kwargs)

        return ToolExecutionResult(
            decision="allow",
            message="Tool executed successfully.",
            result=result,
        )
