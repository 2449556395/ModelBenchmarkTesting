from __future__ import annotations
from .mock import MockClient
from .openai_compatible import OpenAICompatibleClient
from .local_http import LocalHttpClient


def create_client(name: str, models_config: dict):
    cfg = models_config['models'][name]
    typ = cfg.get('type')
    if typ == 'mock':
        return MockClient()
    if typ == 'openai_compatible':
        return OpenAICompatibleClient(cfg)
    if typ == 'local_http':
        return LocalHttpClient(cfg)
    raise ValueError(f'unknown model client type: {typ}')
