"""
Cover letter generator — short email + full cover letter.
"""

from typing import Optional

from src.llm_client import get_llm
from src.models import CoverLetterResult
from src.prompts import get_cover_letter_prompt


def generate_cover_letter(
    cv_text: str,
    job_description: str,
    company_name: str,
    job_title: str,
    tailored_summary: str = "",
    tailored_bullets: Optional[list[str]] = None,
    api_key: Optional[str] = None,
) -> CoverLetterResult:
    """
    Generate a short email message and a full cover letter.

    Uses CV + JD + tailored bullets to produce professional,
    entry-level appropriate application materials.

    Args:
        cv_text: Full extracted CV text.
        job_description: Target job description.
        company_name: Company name.
        job_title: Job title.
        tailored_summary: Optional pre-generated summary.
        tailored_bullets: Optional pre-generated bullet points.
        api_key: Optional Groq API key override.

    Returns:
        CoverLetterResult with email_message and full_cover_letter.
    """
    if not cv_text or not cv_text.strip():
        raise ValueError("CV text is missing. Upload a CV first.")
    job_description = job_description.strip()
    if not job_description:
        raise ValueError("Job description is empty.")

    bullets_str = "\n".join(f"- {b}" for b in (tailored_bullets or [])) or "Not yet generated"

    llm = get_llm(api_key=api_key, temperature=0.4)
    structured_llm = llm.with_structured_output(CoverLetterResult)
    chain = get_cover_letter_prompt() | structured_llm

    return chain.invoke(
        {
            "company_name": company_name,
            "job_title": job_title,
            "job_description": job_description,
            "tailored_summary": tailored_summary or "Not yet generated",
            "tailored_bullets": bullets_str,
            "cv_full_text": cv_text,
        }
    )
