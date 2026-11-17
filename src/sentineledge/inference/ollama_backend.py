
import json
from typing import Any

import httpx


class OllamaBackendError(RuntimeError):
    """Raised when local Ollama inference fails."""


class OllamaBackend:
    """
    Local inference backend powered by Ollama's HTTP API.
    """

    def __init__(
        self,
        model: str = "qwen3.5:0.8b",
        base_url: str = "http://localhost:11434",
        timeout: float = 120.0,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def generate(self, prompt: str) -> str:
        """Generate a regular text response."""

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "stream": False,
            "keep_alive": "5m",
            "options": {
                "temperature": 0.2,
            },
        }

        try:
            response = httpx.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
            )

            response.raise_for_status()
            data = response.json()

            content = data.get("message", {}).get("content")

            if not isinstance(content, str) or not content.strip():
                raise OllamaBackendError(
                    "Ollama returned an empty or invalid response."
                )

            return content.strip()

        except httpx.TimeoutException as exc:
            raise OllamaBackendError(
                "Ollama inference timed out."
            ) from exc

        except httpx.HTTPError as exc:
            raise OllamaBackendError(
                "Could not communicate with the Ollama API."
            ) from exc

        except ValueError as exc:
            raise OllamaBackendError(
                "Ollama returned an invalid JSON response."
            ) from exc

    def generate_structured(
        self,
        prompt: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Generate a JSON response constrained by a JSON Schema.

        The returned dictionary must still be validated
        against the application-level Pydantic model.
        """

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        if not isinstance(schema, dict) or not schema:
            raise ValueError("A valid JSON Schema is required.")

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "format": schema,
            "think": False,
            "stream": False,
            "keep_alive": "5m",
            "options": {
                "temperature": 0,
                "num_predict": 256,
            },
        }

        try:
            response = httpx.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
            )

            response.raise_for_status()
            data = response.json()

            content = data.get("message", {}).get("content")

            if not isinstance(content, str) or not content.strip():
                raise OllamaBackendError(
                    "Ollama returned an empty structured response."
                )

            result = json.loads(content)

            if not isinstance(result, dict):
                raise OllamaBackendError(
                    "Ollama structured response must be a JSON object."
                )

            return result

        except httpx.TimeoutException as exc:
            raise OllamaBackendError(
                "Ollama structured inference timed out."
            ) from exc

        except httpx.HTTPError as exc:
            raise OllamaBackendError(
                "Could not communicate with the Ollama API."
            ) from exc

        except (ValueError, json.JSONDecodeError) as exc:
            raise OllamaBackendError(
                "Ollama returned invalid structured JSON."
            ) from exc
