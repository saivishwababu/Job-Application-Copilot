"""
Job application analyzer using LangChain + OpenAI structured output.

Pipeline:
1. Split CV into chunks and build a vector store (RAG)
2. Retrieve CV excerpts relevant to the job description
3. Send CV context + job description to the LLM
4. Return a validated Pydantic object with all analysis fields
"""

import os
from typing import Optional

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from src.cv_loader import extract_text_from_pdf, split_cv_into_chunks
from src.prompts import get_analysis_prompt
from src.rag import build_cv_vectorstore, retrieve_relevant_cv_context


class JobApplicationAnalysis(BaseModel):
    """Structured output schema for the full application analysis."""

    match_score: int = Field(
        ge=0,
        le=100,
        description="Honest match percentage between CV and job description (0-100)",
    )
    required_skills: list[str] = Field(
        description="Skills and keywords required or preferred in the job description"
    )
    matching_skills: list[str] = Field(
        description="Required skills that the CV demonstrates"
    )
    missing_skills: list[str] = Field(
        description="Required skills or keywords missing or weak in the CV"
    )
    tailored_summary: str = Field(
        description="Resume summary tailored to this job (2-4 sentences)"
    )
    improved_bullets: list[str] = Field(
        description="Exactly 5 improved CV bullet points based on real CV experience"
    )
    cover_letter: str = Field(
        description="Short cover letter draft (~250-400 words)"
    )
    interview_questions: list[str] = Field(
        description="Exactly 10 interview questions based on the job and CV"
    )


def analyze_application(
    pdf_bytes: bytes,
    job_description: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    embedding_model: Optional[str] = None,
) -> JobApplicationAnalysis:
    """
    Run the full analysis pipeline on a CV PDF and job description.

    Args:
        pdf_bytes: Raw bytes of the uploaded CV PDF.
        job_description: Target job description text.
        api_key: OpenAI API key (falls back to OPENAI_API_KEY env var).
        model: Chat model name (falls back to OPENAI_MODEL or gpt-4o-mini).
        embedding_model: Embeddings model (falls back to OPENAI_EMBEDDING_MODEL).

    Returns:
        Validated JobApplicationAnalysis with all eight output sections.
    """
    resolved_api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not resolved_api_key:
        raise ValueError(
            "OpenAI API key is missing. Set OPENAI_API_KEY in your .env file."
        )

    job_description = job_description.strip()
    if not job_description:
        raise ValueError("Job description is empty.")

    # Step 1: Extract and chunk CV text from PDF
    cv_full_text = extract_text_from_pdf(pdf_bytes)
    cv_chunks = split_cv_into_chunks(cv_full_text)

    # Step 2: Embed chunks and store in Chroma (RAG index)
    vectorstore = build_cv_vectorstore(
        chunks=cv_chunks,
        api_key=resolved_api_key,
        embedding_model=embedding_model or os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
    )

    # Step 3: Retrieve CV excerpts most relevant to the job description
    cv_context = retrieve_relevant_cv_context(vectorstore, job_description, k=6)

    # Step 4: Call LLM with structured output
    llm = ChatOpenAI(
        api_key=resolved_api_key,
        model=model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.3,
    )
    structured_llm = llm.with_structured_output(JobApplicationAnalysis)
    prompt = get_analysis_prompt()
    chain = prompt | structured_llm

    result: JobApplicationAnalysis = chain.invoke(
        {
            "job_description": job_description,
            "cv_context": cv_context or cv_full_text[:3000],
            "cv_full_text": cv_full_text,
        }
    )
    return result
