"""
Prompt templates for job application analysis.

Prompts instruct the LLM to stay grounded in the uploaded CV and
never invent experience the candidate does not have.
"""

from langchain_core.prompts import ChatPromptTemplate

ANALYSIS_SYSTEM_MESSAGE = """You are an expert career coach and resume writer helping students and job seekers tailor applications.

CRITICAL RULES — follow these strictly:
1. Only use facts, skills, employers, projects, education, and achievements explicitly present in the CV.
2. NEVER invent employers, job titles, projects, degrees, certifications, metrics, or skills.
3. If the CV lacks evidence for a job requirement, list it under missing_skills — do not fabricate coverage.
4. improved_bullets must rephrase or strengthen REAL experience from the CV; do not add fictional achievements.
5. cover_letter must reference only verifiable details from the CV.
6. interview_questions should be realistic questions based on the job description and what the CV actually shows.
7. match_score (0–100) must reflect honest overlap between CV evidence and job requirements."""

ANALYSIS_USER_MESSAGE = """Analyze the candidate's CV against the target job description.

## Job Description
{job_description}

## Most Relevant CV Excerpts (retrieved via semantic search)
{cv_context}

## Full CV Text (for complete skill and keyword matching)
{cv_full_text}

Produce a structured analysis with:
- match_score: integer 0–100
- required_skills: skills/keywords clearly required or preferred in the job description
- matching_skills: required skills the CV demonstrates with evidence
- missing_skills: required skills/keywords absent or only weakly implied in the CV
- tailored_summary: 2–4 sentence resume summary tailored to this role
- improved_bullets: exactly 5 stronger bullet points based on existing CV content only
- cover_letter: short professional draft (~250–400 words)
- interview_questions: exactly 10 likely interview questions"""


def get_analysis_prompt() -> ChatPromptTemplate:
    """Return the chat prompt template used for structured application analysis."""
    return ChatPromptTemplate.from_messages(
        [
            ("system", ANALYSIS_SYSTEM_MESSAGE),
            ("human", ANALYSIS_USER_MESSAGE),
        ]
    )
