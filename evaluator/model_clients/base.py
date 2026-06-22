from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ModelResponse:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_seconds: float = 0.0
    cost_usd: float = 0.0
    raw: Dict[str, Any] | None = None


class ModelClient:
    def generate(self, prompt: str, task: dict) -> ModelResponse:
        raise NotImplementedError
