from __future__ import annotations
import time
from .base import ModelClient, ModelResponse


class MockClient(ModelClient):
    """Framework smoke-test model. It does not solve tasks; it emits a no-op response."""

    def generate(self, prompt: str, task: dict) -> ModelResponse:
        start = time.time()
        text = (
            "MOCK_RESPONSE\n"
            "This client is intended for framework smoke tests only.\n"
            "No code changes were produced.\n"
        )
        return ModelResponse(
            text=text,
            input_tokens=max(1, len(prompt) // 4),
            output_tokens=max(1, len(text) // 4),
            latency_seconds=time.time() - start,
            cost_usd=0.0,
            raw={'client': 'mock'},
        )
