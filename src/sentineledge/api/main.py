
from sentineledge.safety.permissions import ToolPermissionManager
from sentineledge.tools.registry import ToolExecutor
from sentineledge.tools.calculator import CalculatorTool

from fastapi import FastAPI,HTTPException
from pydantic import BaseModel, Field

from sentineledge.safety.policy_engine import (
    PolicyEngine,
    PolicyDecision,
)
from sentineledge.inference.mock_backend import (
    MockInferenceBackend,
)

from sentineledge.safety.injection_detector import (
    PromptInjectionDetector,
)

from sentineledge.safety.trust_boundary import TrustBoundaryFormatter


class ToolExecuteRequest(BaseModel):
    tool_name: str
    arguments: dict = Field(default_factory=dict)


class ToolExecuteResponse(BaseModel):
    decision: str
    message: str
    result: object | None = None


class ExecuteRequest(BaseModel):
    action: str = Field(default="answer")
    text: str = Field(max_length=10000)
    context: str | None = Field(default=None, max_length=10000)


class ExecuteResponse(BaseModel):
    decision: str
    message: str
    result: str | None = None


def create_app(inference_backend=None):

    app = FastAPI(
        title="SentinelEdge AI",
        description="Safety-aware hybrid AI system",
        version="0.1.0",
    )

    policy_engine = PolicyEngine()
    injection_detector = PromptInjectionDetector()
    trust_boundary = TrustBoundaryFormatter()

    backend = inference_backend or MockInferenceBackend()
    permission_manager = ToolPermissionManager()
    tool_executor = ToolExecutor(permission_manager)

    calculator = CalculatorTool()

    tool_executor.register(
    "calculator",
    calculator.calculate,
    )
    
    @app.post(
    "/api/v1/tools/execute",
    response_model=ToolExecuteResponse,)
    
    def execute_tool(request: ToolExecuteRequest):

        try:
            execution = tool_executor.execute(
                request.tool_name,
                **request.arguments,
            )

            return ToolExecuteResponse(
                decision=execution.decision,
                message=execution.message,
                result=execution.result,
            )

        except TypeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid tool arguments.",
            )

        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=str(exc),
            )
        
    
    
    @app.post(
        "/api/v1/execute",
        response_model=ExecuteResponse,
    )
    def execute(request: ExecuteRequest):
        
        injection_result = injection_detector.detect(request.text)

        if injection_result.is_suspicious:
            return ExecuteResponse(
                decision="deny",
                message="Potential prompt injection detected.",
            )
            
        policy_result = policy_engine.evaluate(
            action=request.action,
            text=request.text,
        )

        if policy_result.decision == PolicyDecision.DENY:
            return ExecuteResponse(
                decision="deny",
                message=policy_result.reason,
            )

        if policy_result.decision == PolicyDecision.REQUIRE_APPROVAL:
            return ExecuteResponse(
                decision="require_approval",
                message=policy_result.reason,
            )

        # Inference is called only after policy approval.
        safe_prompt = trust_boundary.format(
        user_request=request.text,
        untrusted_context=request.context,
        )

        result = backend.generate(safe_prompt)
        # result = backend.generate(request.text)

        return ExecuteResponse(
            decision="allow",
            message=policy_result.reason,
            result=result,
        )

    return app


app = create_app()

