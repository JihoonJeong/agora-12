"""LLM Adapters"""

from .base import BaseLLMAdapter, LLMResponse
from .mock import MockAdapter
from .ollama import OllamaAdapter
from .anthropic import AnthropicAdapter
from .openai import OpenAIAdapter
from .google import GoogleAdapter


# 어댑터 레지스트리
ADAPTER_REGISTRY = {
    "mock": MockAdapter,
    "ollama": OllamaAdapter,
    "anthropic": AnthropicAdapter,
    "openai": OpenAIAdapter,
    "google": GoogleAdapter,
}


def create_adapter(adapter_type: str, **kwargs) -> BaseLLMAdapter:
    """어댑터 팩토리 함수"""
    adapter_class = ADAPTER_REGISTRY.get(adapter_type.lower())
    if adapter_class is None:
        raise ValueError(f"Unknown adapter type: {adapter_type}. Available: {list(ADAPTER_REGISTRY.keys())}")
    return adapter_class(**kwargs)


__all__ = [
    "BaseLLMAdapter",
    "LLMResponse",
    "MockAdapter",
    "OllamaAdapter",
    "AnthropicAdapter",
    "OpenAIAdapter",
    "GoogleAdapter",
    "ADAPTER_REGISTRY",
    "create_adapter",
]
