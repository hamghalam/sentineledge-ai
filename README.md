# SentinelEdge AI

**A Safety-Aware Hybrid Agentic AI System with Cloud and Edge Inference**

SentinelEdge AI is an ongoing engineering project focused on building a modular AI system that combines agentic workflows, application-level security controls, and hybrid cloud/edge inference.

The project explores how AI agents can interact with tools and external context while operating within explicit permission boundaries and safety policies.

> **Project status:** Early development — foundational safety gateway, controlled tool execution, FastAPI endpoints, and initial LangGraph agent orchestration implemented. The current agent uses a deterministic planner and mock inference backend. LLM integration and cloud/edge routing are planned.

## 1. Project Goals

The long-term goals are to:

- Build a safety-aware foundation for agentic AI applications.
- Enforce tool permissions outside the language model.
- Treat retrieved documents and external tool outputs as untrusted data.
- Route inference requests between local edge models and cloud models.
- Evaluate security, latency, throughput, and resource consumption.
- Explore efficient model deployment using ONNX Runtime and quantization.

## 2. Current Architecture

The project currently has two execution paths: the FastAPI endpoints and the LangGraph agent workflow.

### LangGraph Agent Workflow

```text
                  User Input
                      |
                      v
               Input Validation
                      |
                      v
             Prompt Injection Check
                      |
                      v
                   Planner
              (Deterministic)
                      |
                      v
              Safety Supervisor
                      |
              +-------+-------+
              |               |
          Tool Selected    No Tool Needed
              |               |
              v               v
         Tool Executor    Mock Inference
              |               |
              v               |
          Calculator          |
              |               |
              +-------+-------+
                      |
                      v
                   Result
```

### Safety and Tool Execution Components

- Policy Engine
- Prompt Injection Detector
- Trust Boundary Formatter
- Tool Permission Manager
- Centralized Tool Executor

The LangGraph workflow uses these security components to validate input, select a candidate action, authorize tool execution, and produce a result.

## 3. Implemented Components

### Safety Gateway

- **Policy Engine:** Evaluates requested actions and returns `allow`, `deny`, or `require_approval`.
- **Prompt Injection Detector:** Detects selected direct prompt-injection patterns using regular expressions.
- **Trust Boundary Formatter:** Separates the user's request from external context and explicitly labels external content as untrusted.
- **Tool Permission Manager:** Enforces application-level permissions for registered tools.

### Tool Execution Framework

- Centralized tool registry and execution mechanism.
- Read-only and sensitive tool classifications.
- Sensitive tools require approval before execution.
- Calculator tool using Python AST parsing and an operator allowlist instead of `eval()`.
- FastAPI endpoint for controlled tool execution.
- Argument signature validation before tool invocation.
- Duplicate and unauthorized tool registration prevention.

### Agent Orchestration

- LangGraph-based stateful workflow.
- Input validation node.
- Prompt injection detection node.
- Deterministic baseline planner.
- Safety supervisor for tool authorization.
- Controlled tool execution node.
- Direct response node using the mock inference backend.
- Blocked response path for rejected requests.

**Current limitation:** The planner is rule-based and does not use an LLM yet. LangGraph manages the workflow; it does not itself provide the language model.

### Inference API

- FastAPI-based request handling.
- Mock inference backend for development and testing.
- Policy and injection checks before inference.
- Optional external context with trust-boundary formatting.

## 4. API Endpoints

The development server exposes two endpoints.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/execute` | Safety checks and inference |
| POST | `/api/v1/tools/execute` | Permission-controlled tool execution |

Interactive API documentation:

`http://127.0.0.1:8000/docs`

### Example: AI Execution

Request:

```json
{
  "action": "answer",
  "text": "Explain edge AI.",
  "context": "Edge AI processes data close to its source."
}
```

### Example: Calculator Tool

Request:

```json
{
  "tool_name": "calculator",
  "arguments": {
    "expression": "(10 + 5) * 2"
  }
}
```

Expected response:

```json
{
  "decision": "allow",
  "message": "Tool executed successfully.",
  "result": 30
}
```

## 5. Technology Stack

| Area | Technology |
|---|---|
| Programming language | Python 3.12+ |
| API framework | FastAPI |
| Data validation | Pydantic |
| Agent orchestration | LangGraph |
| Testing | Pytest |
| API testing | HTTPX / FastAPI TestClient |
| Tool execution | Python |
| Containerization | Docker — planned |
| Local inference | Ollama / other local inference runtimes — planned |
| Edge inference | ONNX Runtime — planned |
| Model optimization | FP16 / INT8 — planned |

## 6. Local Development

### Requirements

- Python 3.12+
- Git
- PowerShell

### Setup

Clone the repository:

```powershell
git clone https://github.com/hamghalam/sentineledge-ai.git
cd sentineledge-ai
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements-dev.txt
```

Set the source directory:

```powershell
$env:PYTHONPATH = "src"
```

### Run the API

```powershell
python -m uvicorn sentineledge.api.main:app --reload
```

Open:

`http://127.0.0.1:8000/docs`

### Run the LangGraph Agent

The current agent supports basic arithmetic requests through the calculator tool and direct responses through the mock inference backend.

```powershell
$env:PYTHONPATH = "src"

python -c "from sentineledge.agent.graph import build_agent_graph; agent = build_agent_graph(); print(agent.invoke({'user_input': 'What is 10 + 5?'}))"
```

### Run Tests

```powershell
$env:PYTHONPATH = "src"
python -m pytest -v
```

## 7. Security Considerations and Limitations

This project is an experimental engineering prototype, not a production-ready security gateway.

Current limitations include:

- The prompt-injection detector uses a limited set of regular-expression patterns and cannot detect every attack.
- Trust-boundary formatting is a defense-in-depth measure, not a guarantee that an LLM will ignore malicious external instructions.
- The current planner is deterministic and rule-based; LLM-based planning has not yet been implemented.
- The inference backend is currently a mock implementation.
- Sensitive tools currently return `require_approval`; a trusted approval workflow has not yet been implemented.
- The calculator supports a restricted set of arithmetic operations but requires further hardening against resource-exhaustion inputs.
- Authentication, user-level authorization, rate limiting, and production-grade audit logging are not yet implemented.
- The LangGraph workflow is currently a separate agent entry point and has not yet been integrated into the FastAPI execution endpoint.

Security decisions should be enforced by trusted application code rather than relying exclusively on model instructions or model-generated classifications.

## 8. Roadmap

### Phase 1 — Safety and Tool Foundation

- [x] FastAPI application
- [x] Policy engine
- [x] Baseline prompt-injection detector
- [x] Trust-boundary formatter
- [x] Tool permission manager
- [x] Controlled tool executor
- [x] Safe arithmetic calculator
- [x] API and unit tests

### Phase 2 — Agentic AI

- [x] LangGraph-based agent orchestration
- [x] Baseline planner
- [x] Safety supervisor
- [x] Tool selection and execution workflow
- [ ] LLM-based structured planner
- [ ] FastAPI integration for the agent workflow
- [ ] Trusted human-approval mechanism
- [ ] Output validation and grounding

### Phase 3 — Hybrid Cloud and Edge Inference

- [ ] Local LLM integration
- [ ] Cloud inference backend
- [ ] Dynamic edge/cloud routing
- [ ] Latency-, privacy-, and resource-aware routing
- [ ] ONNX Runtime integration where supported

### Phase 4 — Optimization and Evaluation

- [ ] FP16 and INT8 inference optimization
- [ ] CPU/GPU/NPU benchmarking
- [ ] Prompt-injection evaluation
- [ ] Unauthorized tool execution tests
- [ ] Privacy leakage and unsafe-output evaluation
- [ ] Latency, throughput, and memory profiling

## 9. Security and Research References

- [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- [MITRE ATLAS](https://atlas.mitre.org/)
- [NVIDIA garak](https://github.com/NVIDIA/garak)

---

**Author:** Mohammad Hamghalam  
**Repository:** https://github.com/hamghalam/sentineledge-ai
