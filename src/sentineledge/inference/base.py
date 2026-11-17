
from typing import Protocol


class InferenceBackend(Protocol):
    """
    Common interface for inference backends.

    Implementations may use local models, cloud models,
    or mock responses for testing.
    """

    def generate(self, prompt: str) -> str:
        ...
