
import httpx
import pytest

from sentineledge.inference.ollama_backend import (
    OllamaBackend,
    OllamaBackendError,
)


def test_ollama_backend_generates_response(monkeypatch):
    def fake_post(url, json, timeout):
        assert url == "http://localhost:11434/api/chat"
        assert json["model"] == "qwen3.5:0.8b"
        assert json["stream"] is False

        return httpx.Response(
            200,
            json={
                "message": {
                    "content": "Edge AI runs models locally."
                }
            },
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    backend = OllamaBackend()
    result = backend.generate("Explain Edge AI.")

    assert result == "Edge AI runs models locally."


def test_ollama_backend_rejects_empty_prompt():
    backend = OllamaBackend()

    with pytest.raises(ValueError):
        backend.generate("")


def test_ollama_backend_handles_connection_error(monkeypatch):
    def fake_post(*args, **kwargs):
        raise httpx.ConnectError("Connection refused")

    monkeypatch.setattr(httpx, "post", fake_post)

    backend = OllamaBackend()

    with pytest.raises(OllamaBackendError):
        backend.generate("Explain Edge AI.")


def test_ollama_backend_handles_timeout(monkeypatch):
    def fake_post(*args, **kwargs):
        raise httpx.TimeoutException("Request timed out")

    monkeypatch.setattr(httpx, "post", fake_post)

    backend = OllamaBackend()

    with pytest.raises(OllamaBackendError):
        backend.generate("Explain Edge AI.")


def test_ollama_backend_rejects_empty_response(monkeypatch):
    def fake_post(url, **kwargs):
        return httpx.Response(
            200,
            json={"message": {"content": ""}},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    backend = OllamaBackend()

    with pytest.raises(OllamaBackendError):
        backend.generate("Explain Edge AI.")
