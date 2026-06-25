"""
Initial application analysis — skills extraction, fit score, and gaps.

Used by the Upload & Analyze tab. Combines JD parsing with CV comparison.
"""

from typing import Optional

from pydantic import BaseModel, Field

from src.cv_context import build_cv_rag_context
from src.cv_loader import extract_text_from_pdf
from src.jd_parser import parse_job_description
from src.llm_client import get_llm
from src.models import FitAnalysis, JDExtraction
from src.prompts import get_analysis_prompt


class AnalysisResult(BaseModel):
    """Combined output for the Upload & Analyze tab."""

    cv_text: str
    jd_extraction: JDExtraction
    fit_analysis: FitAnalysis


def analyze_application(
    job_description: str,
    company_name: str = "",
    job_title: str = "",
    pdf_bytes: bytes | None = None,
    cv_text: str | None = None,
    api_key: Optional[str] = None,
) -> AnalysisResult:
    """
    Run the full analysis pipeline: extract CV, parse JD, compute fit score.

    Provide either pdf_bytes (fresh upload) or cv_text (already extracted).
    """
    job_description = job_description.strip()
    if not job_description:
        raise ValueError("Job description is empty.")

    if cv_text and cv_text.strip():
        cv_full_text = cv_text.strip()
    elif pdf_bytes:
        cv_full_text = extract_text_from_pdf(pdf_bytes)
    else:
        raise ValueError("Provide either pdf_bytes or cv_text.")
    cv_context = build_cv_rag_context(cv_full_text, job_description)

    # Extract skills/requirements from JD
    jd_extraction = parse_job_description(job_description, api_key=api_key)

    # Compare CV against JD for fit score and gaps
    llm = get_llm(api_key=api_key)
    structured_llm = llm.with_structured_output(FitAnalysis)
    chain = get_analysis_prompt() | structured_llm

    fit_analysis: FitAnalysis = chain.invoke(
        {
            "company_name": company_name or "Not specified",
            "job_title": job_title or "Not specified",
            "job_description": job_description,
            "cv_context": cv_context,
            "cv_full_text": cv_full_text,
        }
    )

    return AnalysisResult(
        cv_text=cv_full_text,
        jd_extraction=jd_extraction,
        fit_analysis=fit_analysis,
    )
