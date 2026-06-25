"""
Resume tailoring — fit score, skill gaps, and improved bullets.
"""

from typing import Optional

from src.cv_context import build_cv_rag_context
from src.llm_client import get_llm
from src.models import TailoringResult
from src.prompts import get_tailoring_prompt


def tailor_resume(
    cv_text: str,
    job_description: str,
    company_name: str,
    job_title: str,
    required_skills: Optional[list[str]] = None,
    api_key: Optional[str] = None,
) -> TailoringResult:
    """
    Tailor resume content for a specific job application.

    Compares CV against JD, identifies gaps, and rewrites the most
    relevant bullets — grounded in real CV content only.

    Args:
        cv_text: Full extracted CV text.
        job_description: Target job description.
        company_name: Company name for context.
        job_title: Job title for context.
        required_skills: Pre-extracted skills (optional; shown in prompt).
        api_key: Optional Groq API key override.

    Returns:
        TailoringResult with summary, bullets, and fit analysis.
    """
    if not cv_text or not cv_text.strip():
        raise ValueError("CV text is missing. Upload a CV first.")
    job_description = job_description.strip()
    if not job_description:
        raise ValueError("Job description is empty.")

    cv_context = build_cv_rag_context(cv_text, job_description)
    skills_str = ", ".join(required_skills) if required_skills else "See job description"

    llm = get_llm(api_key=api_key)
    structured_llm = llm.with_structured_output(TailoringResult)
    chain = get_tailoring_prompt() | structured_llm

    return chain.invoke(
        {
            "company_name": company_name,
            "job_title": job_title,
            "job_description": job_description,
            "required_skills": skills_str,
            "cv_context": cv_context,
            "cv_full_text": cv_text,
        }
    )
