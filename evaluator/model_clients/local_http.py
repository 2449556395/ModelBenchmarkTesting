from __future__ import annotations
import json, time, urllib.request
from .base import ModelClient, ModelResponse


class LocalHttpClient(ModelClient):
    def __init__(self, config: dict):
        self.config = config

    def generate(self, prompt: str, task: dict) -> ModelResponse:
        payload = {'prompt': prompt, 'task': task.get('id')}
        req = urllib.request.Request(self.config['url'], data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
        start = time.time()
        with urllib.request.urlopen(req, timeout=self.config.get('timeout_seconds', 120)) as resp:
            raw = json.loads(resp.read().decode('utf-8'))
        text = raw.get('text') or raw.get('response') or raw.get('content') or ''
        return ModelResponse(text=text, input_tokens=raw.get('input_tokens', 0), output_tokens=raw.get('output_tokens', 0), latency_seconds=time.time() - start, cost_usd=raw.get('cost_usd', 0.0), raw=raw)
