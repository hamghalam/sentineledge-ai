# SentinelEdge AI

**A Safety-Aware Hybrid Agentic AI System with Cloud and Edge Inference**

SentinelEdge AI is an experimental engineering project exploring the intersection of **Agentic AI, AI Safety, and Edge AI**.

It combines structured LLM-based planning, controlled tool execution, application-level security enforcement, and modular inference backends.

The central design principle is that **an AI model may propose an action, but trusted application code decides whether that action is permitted and whether it can execute.**

The long-term objective is to develop a hybrid AI architecture capable of intelligently distributing workloads between local edge devices and cloud inference services while considering security, privacy, latency, and computational resources.

> **Project status:** Active development. The foundational safety gateway, LangGraph orchestration, structured local LLM planning, Ollama inference backend, and tool-specific argument validation are implemented.

---

## 1. Project Goals

The project aims to:

- Build a modular and safety-aware agentic AI architecture.
- Separate LLM-generated proposals from application-level authorization.
- Enforce tool permissions outside the language model.
- Validate tool arguments before execution.
- Treat external documents and retrieved content as untrusted data.
- Support interchangeable inference backends.
- Explore privacy-aware and resource-aware edge/cloud inference routing.
- Evaluate security, latency, throughput, and resource consumption.
- Investigate efficient model deployment using ONNX Runtime and quantization.

## 2. System Architecture

The system is organized into independent components with clearly defined responsibilities.

### High-Level Architecture

```text
                    User Request
                         |
                         v
                 FastAPI / Agent Entry
                         |
                         v
                 Safety Gateway
                         |
              +----------+----------+
              |                     |
              v                     v
        Input Validation      Injection Detection
              |                     |
              +----------+----------+
                         |
                         v
                  Agent Orchestrator
                      LangGraph
                         |
                         v
                    LLM Planner
                  (Structured Output)
                         |
                         v
                 Pydantic Validation
                         |
                         v
                 Safety Supervisor
                         |
                  Permission Check
                         |
              +----------+----------+
              |                     |
              v                     v
         Tool Executor         Direct Response
              |                     |
       Argument Validation          |
              |                     |
              v                     v
          Calculator          Inference Backend
                                    |
                          +---------+---------+
                          |                   |
                          v                   v
                     Local LLM          Future Cloud LLM
                       Ollama
                          |
                          v
                    Final Response
```

The LangGraph agent supports both a deterministic baseline planner and an LLM-based structured planner.

### Core Design Principles

**1. Separation of planning and authorization**

The LLM planner proposes actions but cannot authorize or execute them.

**2. Independent security enforcement**

Tool permissions and argument validation are enforced by trusted application code.

**3. Fail-closed execution**

Planner failures and authorization failures must not result in tool execution.

**4. Modular inference**

Inference backends follow a common interface, allowing mock and local model implementations to be used independently.

---

## 3. Implemented Components

### 3.1 Safety Gateway

| Component | Responsibility |
|---|---|
| Policy Engine | Evaluates requests and returns `allow`, `deny`, or `require_approval`. |
| Prompt Injection Detector | Detects selected direct prompt-injection patterns using regular expressions. |
| Trust Boundary Formatter | Separates user instructions from untrusted external context. |
| Tool Permission Manager | Enforces application-level tool permissions. |

The security layer is independent of LLM-generated authorization decisions.

### 3.2 Tool Execution Framework

The centralized `ToolExecutor` controls tool registration and execution.

Implemented capabilities:

- Application-level tool permission checks.
- Read-only and sensitive tool classifications.
- Prevention of unauthorized tool registration.
- Duplicate registration prevention.
- Callable validation.
- Function signature validation.
- Tool-specific Pydantic argument validation.
- Prevention of execution when arguments are invalid.

The current calculator tool supports basic arithmetic using Python AST parsing and an explicit operator allowlist instead of `eval()`.

**Example validation contract:**

```python
class CalculatorArgs(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    expression: str = Field(
        min_length=1,
        max_length=100,
    )
```

The same argument schema is shared by the planner and tool execution layer.

### 3.3 Agent Orchestration

The agent uses LangGraph to coordinate the execution workflow.

Implemented nodes:

- Input validation
- Prompt injection detection
- Deterministic planner
- LLM planner
- Safety supervisor
- Controlled tool execution
- Direct response
- Blocked response

The planner can select between:

- `direct_response`
- `tool_call`

The LLM planner generates structured proposals that are validated using Pydantic before being passed to the safety supervisor.

A planner failure results in a blocked request rather than unauthorized execution.

### 3.4 Local LLM Integration

Local inference is implemented through Ollama.

Current configuration:

| Component | Configuration |
|---|---|
| Runtime | Ollama |
| Model | Qwen 3.5 0.8B |
| Backend | `OllamaBackend` |
| Communication | HTTP API |
| Structured output | JSON Schema |
| Validation | Pydantic |
| Temperature | 0 |

The local model is used for:

- Structured task planning.
- Tool selection.
- Tool argument generation.
- Direct response generation.

The inference layer provides a common backend interface, with a mock implementation for testing and an Ollama implementation for real local inference.

The current development environment has successfully run the Qwen model using GPU inference.

### 3.5 Inference API

The FastAPI application currently provides two endpoints:

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/execute` | Safety checks and inference |
| POST | `/api/v1/tools/execute` | Permission-controlled tool execution |

The API and LangGraph agent are currently separate execution entry points. The agent's local LLM integration is not yet exposed through the FastAPI endpoints.

---

## 4. Technology Stack

| Area | Technology |
|---|---|
| Programming language | Python 3.12+ |
| API framework | FastAPI |
| Data validation | Pydantic |
| Agent orchestration | LangGraph |
| Local inference runtime | Ollama |
| Local LLM | Qwen 3.5 0.8B |
| HTTP communication | HTTPX |
| Testing | Pytest |
| API testing | HTTPX / FastAPI TestClient |
| Tool execution | Python AST |
| Version control | Git / GitHub |
| Future edge inference | ONNX Runtime |
| Future model optimization | FP16 / INT8 |

---

## 5. Local Development Setup

### Requirements

- Python 3.12+
- Git
- PowerShell
- Ollama (for local LLM inference)

### Clone the Repository

```powershell
git clone https://github.com/hamghalam/sentineledge-ai.git
cd sentineledge-ai
```

### Create a Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Install Dependencies

```powershell
python -m pip install -r requirements-dev.txt
```

### Configure Python Path

```powershell
$env:PYTHONPATH = "src"
```

### Run the API

```powershell
python -m uvicorn sentineledge.api.main:app --reload
```

Interactive API documentation:

http://127.0.0.1:8000/docs

### Configure Local Inference

Install Ollama from:

https://ollama.com/

Download the model:

```powershell
ollama pull qwen3.5:0.8b
```

Ensure the Ollama service is running.

### Run the LangGraph Agent with the Mock Backend

```powershell
python -c "from sentineledge.agent.graph import build_agent_graph; agent = build_agent_graph(); print(agent.invoke({'user_input': 'What is 10 + 5?'}))"
```

### Run the LangGraph Agent with Ollama

```powershell
@'
from sentineledge.inference.ollama_backend import OllamaBackend
from sentineledge.agent.planner import LLMPlanner
from sentineledge.agent.graph import build_agent_graph

backend = OllamaBackend(model="qwen3.5:0.8b")
planner = LLMPlanner(backend)

agent = build_agent_graph(
    inference_backend=backend,
    planner_backend=planner,
)

result = agent.invoke({
    "user_input": "What is 125 multiplied by 8?"
})

print(result)
'@ | python
```

The agent should use the local LLM to generate a structured calculator proposal, validate it, authorize the tool, and execute the calculation.

### Run Tests

Run the complete test suite:

```powershell
python -m pytest -v
```

Run individual security tests:

```powershell
python -m pytest tests/test_llm_planner_security.py -v
python -m pytest tests/test_tool_permissions.py -v
```

---

## 6. Security Architecture and Limitations

SentinelEdge AI is an experimental engineering prototype, not a production-ready security gateway.

Important security considerations:

- The prompt-injection detector uses a limited set of regular-expression patterns and cannot detect every attack.
- Trust-boundary formatting is defense-in-depth, not a guarantee that an LLM will ignore malicious external instructions.
- Structured output and Pydantic validation constrain planner proposals but do not establish that the proposed action is safe.
- Authorization is enforced separately by application code.
- Sensitive tools currently return `require_approval`; a trusted human-approval workflow has not yet been implemented.
- The calculator supports a restricted set of arithmetic operations but requires further hardening against resource-exhaustion inputs.
- Authentication, user-level authorization, rate limiting, and production-grade audit logging are not yet implemented.
- The LangGraph agent is not yet integrated into the FastAPI execution endpoint.
- Cloud inference and dynamic edge/cloud routing have not yet been implemented.

Security decisions should be enforced by trusted application code rather than relying exclusively on model instructions or model-generated classifications.

---

## 7. Development Roadmap

### Phase 1 — Safety and Tool Foundation

- [x] FastAPI application
- [x] Policy engine
- [x] Baseline prompt-injection detector
- [x] Trust-boundary formatter
- [x] Tool permission manager
- [x] Controlled tool executor
- [x] Safe arithmetic calculator
- [x] Function signature validation
- [x] Tool-specific Pydantic argument validation
- [x] API and unit tests

### Phase 2 — Agentic AI and Local LLM

- [x] LangGraph-based agent orchestration
- [x] Deterministic baseline planner
- [x] Safety supervisor
- [x] Controlled tool selection and execution
- [x] Structured LLM planner
- [x] Pydantic planner validation
- [x] Ollama inference backend
- [x] Local Qwen integration
- [x] Planner failure handling
- [x] Security tests for planner and tool execution
- [ ] FastAPI integration for the agent workflow
- [ ] Trusted human-approval mechanism
- [ ] Output validation and grounding

### Phase 3 — Hybrid Cloud and Edge Inference

- [x] Local LLM inference
- [x] Modular inference backend interface
- [ ] Cloud inference backend
- [ ] Dynamic edge/cloud routing
- [ ] Latency-, privacy-, and resource-aware routing
- [ ] ONNX Runtime integration where supported

### Phase 4 — Optimization and Evaluation

- [ ] FP16 and INT8 inference optimization
- [ ] CPU/GPU/NPU benchmarking
- [ ] Prompt-injection evaluation
- [ ] Unauthorized tool execution evaluation
- [ ] Privacy leakage and unsafe-output evaluation
- [ ] Latency, throughput, and memory profiling
- [ ] Performance comparison between local and cloud inference

---

## 8. Security and Research References

- [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- [MITRE ATLAS](https://atlas.mitre.org/)
- [NVIDIA garak](https://github.com/NVIDIA/garak)

---

**Author:** Mohammad Hamghalam

**Repository:** https://github.com/hamghalam/sentineledge-ai
