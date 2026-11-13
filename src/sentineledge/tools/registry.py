from dataclasses import dataclass
from typing import Callable, Any

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
        self.tools: dict[str, Callable] = {}

    def register(self, name: str, function: Callable):
        if name not in self.permission_manager.TOOL_PERMISSIONS:
            raise ValueError(f"Tool '{name}' is not in the permission policy.")

        self.tools[name] = function

    def execute(self, name: str, **kwargs) -> ToolExecutionResult:
        authorization = self.permission_manager.authorize(name)

        if authorization.decision != AuthorizationDecision.ALLOW:
            return ToolExecutionResult(
                decision=authorization.decision.value,
                message=authorization.reason,
            )

        function = self.tools.get(name)

        if function is None:
            return ToolExecutionResult(
                decision="deny",
                message="Tool is registered in policy but has no implementation.",
            )

        result = function(**kwargs)

        return ToolExecutionResult(
            decision="allow",
            message="Tool executed successfully.",
            result=result,
        )