from dataclasses import dataclass
from inspect import signature
from typing import Any, Callable, Type

from pydantic import BaseModel, ValidationError

from sentineledge.safety.permissions import (
    ToolPermissionManager,
    AuthorizationDecision,
)
from sentineledge.tools.schemas import CalculatorArgs


@dataclass
class ToolExecutionResult:
    decision: str
    message: str
    result: Any = None


@dataclass
class RegisteredTool:
    function: Callable[..., Any]
    argument_model: Type[BaseModel] | None = None


class ToolExecutor:
    # Trusted application-side schemas for registered tools.
    TOOL_ARGUMENT_MODELS = {
        "calculator": CalculatorArgs,
    }

    def __init__(self, permission_manager: ToolPermissionManager):
        self.permission_manager = permission_manager
        self.tools: dict[str, RegisteredTool] = {}

    def register(
        self,
        name: str,
        function: Callable[..., Any],
        argument_model: Type[BaseModel] | None = None,
    ):
        if name not in self.permission_manager.TOOL_PERMISSIONS:
            raise ValueError(
                f"Tool '{name}' is not in the permission policy."
            )

        if not callable(function):
            raise TypeError("Registered tool must be callable.")

        if name in self.tools:
            raise ValueError(f"Tool '{name}' is already registered.")

        # Use the trusted built-in schema unless one is explicitly supplied.
        if argument_model is None:
            argument_model = self.TOOL_ARGUMENT_MODELS.get(name)

        self.tools[name] = RegisteredTool(
            function=function,
            argument_model=argument_model,
        )

    def execute(self, name: str, **kwargs) -> ToolExecutionResult:

        # 1. Authorization must pass before tool lookup or execution.
        authorization = self.permission_manager.authorize(name)

        if authorization.decision != AuthorizationDecision.ALLOW:
            return ToolExecutionResult(
                decision=authorization.decision.value,
                message=authorization.reason,
            )

        # 2. Verify that the tool has an implementation.
        registered_tool = self.tools.get(name)

        if registered_tool is None:
            return ToolExecutionResult(
                decision="deny",
                message="Tool is registered in policy but has no implementation.",
            )

        function = registered_tool.function

        # 3. Validate the function signature.
        try:
            signature(function).bind(**kwargs)
        except TypeError as exc:
            raise TypeError(
                f"Invalid arguments for tool '{name}'."
            ) from exc

        # 4. Validate argument values against the trusted tool schema.
        if registered_tool.argument_model is not None:
            try:
                validated_args = (
                    registered_tool.argument_model.model_validate(kwargs)
                )
                kwargs = validated_args.model_dump()

            except ValidationError:
                return ToolExecutionResult(
                    decision="deny",
                    message=f"Invalid input for tool '{name}'.",
                )

        # 5. Execute only after authorization and validation.
        result = function(**kwargs)

        return ToolExecutionResult(
            decision="allow",
            message="Tool executed successfully.",
            result=result,
        )