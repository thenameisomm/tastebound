from __future__ import annotations

from tastebound_api.llm.base import LLMProvider
from tastebound_api.llm.openai_compat import OpenAICompatibleProvider
from tastebound_api.settings import Settings, get_settings

_provider: LLMProvider | None = None
_provider_ready = False


def _build_provider(settings: Settings) -> LLMProvider | None:
    if settings.llm_provider == "ollama_cloud" and settings.ollama_api_key:
        return OpenAICompatibleProvider(
            base_url=settings.ollama_base_url,
            api_key=settings.ollama_api_key,
            model=settings.ollama_model,
            timeout=settings.llm_timeout_seconds,
            label="ollama_cloud",
        )
    if settings.llm_provider == "openai_compat" and settings.openai_compat_api_key:
        return OpenAICompatibleProvider(
            base_url=settings.openai_compat_base_url,
            api_key=settings.openai_compat_api_key,
            model=settings.openai_compat_model,
            timeout=settings.llm_timeout_seconds,
            label="openai_compat",
        )
    if settings.llm_provider == "gemini" and settings.gemini_api_key:
        return OpenAICompatibleProvider(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai",
            api_key=settings.gemini_api_key,
            model=settings.gemini_model or "gemini-2.5-flash",
            timeout=settings.llm_timeout_seconds,
            label="gemini",
        )
    return None


def get_provider(settings: Settings | None = None) -> LLMProvider | None:
    global _provider, _provider_ready
    if not _provider_ready:
        _provider = _build_provider(settings or get_settings())
        _provider_ready = True
    return _provider


def reset_provider_cache() -> None:
    global _provider, _provider_ready
    _provider = None
    _provider_ready = False
