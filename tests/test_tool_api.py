from fastapi.testclient import TestClient

from sentineledge.api.main import create_app


def test_api_executes_calculator():
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/tools/execute",
        json={
            "tool_name": "calculator",
            "arguments": {
                "expression": "(10 + 5) * 2"
            },
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["decision"] == "allow"
    assert data["result"] == 30


def test_api_blocks_sensitive_tool():
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/tools/execute",
        json={
            "tool_name": "send_email",
            "arguments": {
                "recipient": "test@example.com",
                "message": "Hello",
            },
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["decision"] == "require_approval"
    assert data["result"] is None


def test_api_denies_unknown_tool():
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/tools/execute",
        json={
            "tool_name": "execute_shell",
            "arguments": {},
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["decision"] == "deny"
    assert data["result"] is None