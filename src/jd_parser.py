"""
Job description parser — extract skills and requirements from a JD.
"""

from typing import Optional

from src.llm_client import get_llm
from src.models import JDExtraction
from src.prompts import get_jd_parser_prompt


def parse_job_description(
    job_description: str,
    api_key: Optional[str] = None,
) -> JDExtraction:
    """
    Extract required skills and key requirements from a job description.

    Args:
        job_description: Full job posting text.
        api_key: Optional Groq API key override.

    Returns:
        JDExtraction with skills and requirements lists.
    """
    job_description = job_description.strip()
    if not job_description:
        raise ValueError("Job description is empty.")

    llm = get_llm(api_key=api_key)
    structured_llm = llm.with_structured_output(JDExtraction)
    chain = get_jd_parser_prompt() | structured_llm

    return chain.invoke({"job_description": job_description})
