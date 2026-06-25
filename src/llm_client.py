"""
Centralized Groq LLM client for all modules.

Every feature module calls get_llm() so model and API key
configuration lives in one place.
"""

import os
from functools import lru_cache
from typing import Optional

from langchain_groq import ChatGroq


def get_groq_api_key(api_key: Optional[str] = None) -> str:
    """Return a valid Groq API key or raise a clear error."""
    resolved = api_key or os.getenv("GROQ_API_KEY")
    if not resolved or resolved.strip() in ("", "gsk-your-groq-api-key-here"):
        raise ValueError(
            "Groq API key is missing. Set GROQ_API_KEY in your .env file."
        )
    return resolved.strip()


@lru_cache(maxsize=1)
def _cached_llm(api_key: str, model: str, temperature: float) -> ChatGroq:
    """Internal cached LLM instance (keyed by config)."""
    return ChatGroq(api_key=api_key, model=model, temperature=temperature)


def get_llm(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.3,
) -> ChatGroq:
    """
    Return a configured ChatGroq instance.

    Args:
        api_key: Optional override; defaults to GROQ_API_KEY env var.
        model: Optional override; defaults to GROQ_MODEL or llama-3.3-70b-versatile.
        temperature: Sampling temperature for generation.
    """
    resolved_key = get_groq_api_key(api_key)
    resolved_model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    return _cached_llm(resolved_key, resolved_model, temperature)
