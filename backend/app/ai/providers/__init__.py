import logging
from typing import Optional
from app.core.config import settings
from app.ai.providers.base import BaseLLMProvider
from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.groq import GroqProvider
from app.ai.providers.mock import MockLLMProvider

logger = logging.getLogger(__name__)


def is_valid_gemini_key(key: Optional[str]) -> bool:
    if not key:
        return False
    clean = key.strip()
    return clean.startswith("AIza") and len(clean) >= 30


def is_valid_groq_key(key: Optional[str]) -> bool:
    if not key:
        return False
    clean = key.strip()
    return clean.startswith("gsk_") and len(clean) >= 30


def get_llm_provider(force_provider: str = None) -> BaseLLMProvider:
    provider_name = (force_provider or settings.AI_PROVIDER or "").lower().strip()

    if provider_name == "gemini":
        if is_valid_gemini_key(settings.GEMINI_API_KEY):
            return GeminiProvider(api_key=settings.GEMINI_API_KEY, model_name=settings.GEMINI_MODEL)
        else:
            return MockLLMProvider()

    elif provider_name == "groq":
        if is_valid_groq_key(settings.GROQ_API_KEY):
            return GroqProvider(api_key=settings.GROQ_API_KEY, model_name=settings.GROQ_MODEL)
        else:
            return MockLLMProvider()

    return MockLLMProvider()


__all__ = ["BaseLLMProvider", "GeminiProvider", "GroqProvider", "MockLLMProvider", "get_llm_provider"]
