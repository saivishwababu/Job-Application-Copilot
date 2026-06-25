"""
CV RAG context builder — shared across analysis modules.
"""

import os
from typing import Optional

from src.cv_loader import split_cv_into_chunks
from src.rag import build_cv_vectorstore, retrieve_relevant_cv_context


def build_cv_rag_context(
    cv_full_text: str,
    job_description: str,
    k: int = 6,
    embedding_model: Optional[str] = None,
) -> str:
    """
    Chunk the CV, embed locally, and retrieve excerpts relevant to the JD.

    Returns formatted context string for LLM prompts.
    """
    chunks = split_cv_into_chunks(cv_full_text)
    vectorstore = build_cv_vectorstore(
        chunks=chunks,
        embedding_model=embedding_model
        or os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
    )
    context = retrieve_relevant_cv_context(vectorstore, job_description, k=k)
    return context or cv_full_text[:3000]
