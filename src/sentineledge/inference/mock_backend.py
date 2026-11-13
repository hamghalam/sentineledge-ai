
class MockInferenceBackend:

    def generate(self, prompt: str) -> str:
        """
        Simulates an AI model response.
        No real LLM is called at this stage.
        """
        return f"Mock AI response: {prompt[:100]}"
