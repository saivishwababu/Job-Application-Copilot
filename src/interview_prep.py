"""
Interview preparation — questions with grounded suggested answers.

Uses a loose string schema for question_type to avoid Groq API validation
errors, then normalizes types before returning the final result.
"""

from typing import Optional

from src.cv_context import build_cv_rag_context
from src.llm_client import get_llm
from src.models import InterviewPrepRaw, InterviewPrepResult, InterviewQA
from src.prompts import get_interview_prompt
from src.utils import normalize_question_type


def _normalize_prep_result(raw: InterviewPrepRaw) -> InterviewPrepResult:
    """Convert raw LLM output to validated InterviewPrepResult."""
    questions: list[InterviewQA] = []
    for item in raw.questions:
        try:
            questions.append(
                InterviewQA(
                    question=item.question,
                    suggested_answer=item.suggested_answer,
                    question_type=normalize_question_type(item.question_type),  # type: ignore[arg-type]
                )
            )
        except Exception:
            # Skip malformed entries rather than crashing the whole tab
            continue

    if not questions:
        raise ValueError("No valid interview questions were generated. Please try again.")

    return InterviewPrepResult(questions=questions)


def generate_interview_prep(
    cv_text: str,
    job_description: str,
    company_name: str,
    job_title: str,
    required_skills: Optional[list[str]] = None,
    api_key: Optional[str] = None,
) -> InterviewPrepResult:
    """
    Generate interview questions with suggested answers grounded in the CV.
    """
    if not cv_text or not cv_text.strip():
        raise ValueError("CV text is missing. Upload a CV first.")
    job_description = job_description.strip()
    if not job_description:
        raise ValueError("Job description is empty.")

    cv_context = build_cv_rag_context(cv_text, job_description)
    skills_str = ", ".join(required_skills) if required_skills else "See job description"

    llm = get_llm(api_key=api_key, temperature=0.4)
    # Use loose string schema — Groq rejects invalid enum values at the API level
    structured_llm = llm.with_structured_output(InterviewPrepRaw)
    chain = get_interview_prompt() | structured_llm

    raw: InterviewPrepRaw = chain.invoke(
        {
            "company_name": company_name,
            "job_title": job_title,
            "job_description": job_description,
            "required_skills": skills_str,
            "cv_context": cv_context,
            "cv_full_text": cv_text,
        }
    )
    return _normalize_prep_result(raw)
