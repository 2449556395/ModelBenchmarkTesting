from __future__ import annotations

import json
import os
import time
import urllib.request

from .base import ModelClient, ModelResponse


class OpenAICompatibleClient(ModelClient):
    def __init__(self, config: dict):
        self.config = config

    def generate(self, prompt: str, task: dict) -> ModelResponse:
        # CLI can use api_key_env; Web UI injects api_key in memory only.
        api_key = self.config.get("api_key") or os.environ.get(self.config.get("api_key_env", ""))
        if not api_key:
            raise RuntimeError(f"missing API key; set api_key or env: {self.config.get('api_key_env')}")

        payload = {
            "model": self.config["model"],
            "messages": [
                {
                    "role": "system",
                    "content": "You are a senior software engineer. Return a clear patch or file edit instructions.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": self.config.get("temperature", 0.2),
        }

        reasoning_effort = self.config.get("reasoning_effort") or self.config.get("thinking_level")
        if reasoning_effort and str(reasoning_effort).lower() not in {"none", "off", "default"}:
            payload["reasoning_effort"] = reasoning_effort

        if self.config.get("max_tokens"):
            payload["max_tokens"] = int(self.config["max_tokens"])

        req = urllib.request.Request(
            self.config["base_url"],
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )

        start = time.time()
        with urllib.request.urlopen(req, timeout=self.config.get("timeout_seconds", 120)) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
        latency = time.time() - start

        choice = raw.get("choices", [{}])[0]
        text = choice.get("message", {}).get("content", "") or choice.get("text", "")
        usage = raw.get("usage", {})
        input_tokens = int(usage.get("prompt_tokens", 0))
        output_tokens = int(usage.get("completion_tokens", 0))
        cost = (
            (input_tokens / 1000.0) * self.config.get("input_cost_per_1k", 0.0)
            + (output_tokens / 1000.0) * self.config.get("output_cost_per_1k", 0.0)
        )

        return ModelResponse(
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_seconds=latency,
            cost_usd=cost,
            raw=raw,
        )