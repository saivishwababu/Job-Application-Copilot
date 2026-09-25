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
    if not resolved:
        try:
            import streamlit as st
            resolved = st.secrets.get("GROQ_API_KEY")
        except Exception:
            pass
    if not resolved or resolved.strip() in ("", "gsk-your-groq-api-key-here"):
        raise ValueError(
            "Groq API key is missing. Set GROQ_API_KEY in your .env file or Streamlit Secrets."
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
        api_key: Optional override; defaults to GROQ_API_KEY env var or secrets.
        model: Optional override; defaults to GROQ_MODEL or openai/gpt-oss-120b.
        temperature: Sampling temperature for generation.
    """
    resolved_key = get_groq_api_key(api_key)
    model_env = os.getenv("GROQ_MODEL")
    if not model_env:
        try:
            import streamlit as st
            model_env = st.secrets.get("GROQ_MODEL")
        except Exception:
            pass
    resolved_model = model or model_env or "openai/gpt-oss-120b"
    return _cached_llm(resolved_key, resolved_model, temperature)
