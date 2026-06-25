"""
Prompt templates for all V1 features.

All prompts instruct the LLM to stay grounded in the uploaded CV.
"""

from langchain_core.prompts import ChatPromptTemplate

# ---------------------------------------------------------------------------
# Shared grounding rules (referenced in system messages)
# ---------------------------------------------------------------------------

GROUNDING_RULES = """CRITICAL RULES — follow strictly:
1. Only use facts, skills, employers, projects, education, and achievements explicitly present in the CV.
2. NEVER invent employers, job titles, projects, degrees, certifications, metrics, or skills.
3. If the CV lacks evidence for a requirement, say so honestly — do not fabricate coverage.
4. All rewritten bullets and answers must be grounded in real CV content.
5. Write in a professional, concise tone suitable for students and entry-level roles."""

# ---------------------------------------------------------------------------
# Job description parsing
# ---------------------------------------------------------------------------

JD_PARSER_SYSTEM = f"""You are an expert at reading job descriptions and extracting structured requirements.
{GROUNDING_RULES}"""

JD_PARSER_USER = """Extract required skills and key requirements from this job description.

## Job Description
{job_description}

Return:
- required_skills: technical and soft skills explicitly required or preferred
- extracted_requirements: responsibilities, qualifications, education, and experience requirements"""


def get_jd_parser_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [("system", JD_PARSER_SYSTEM), ("human", JD_PARSER_USER)]
    )


# ---------------------------------------------------------------------------
# Initial analysis (Upload & Analyze tab)
# ---------------------------------------------------------------------------

ANALYSIS_SYSTEM = f"""You are an expert career coach helping students tailor job applications.
{GROUNDING_RULES}
6. fit_score (0–100) must reflect honest overlap between CV evidence and job requirements."""

ANALYSIS_USER = """Analyze the candidate's CV against this job.

## Company / Role
{company_name} — {job_title}

## Job Description
{job_description}

## Relevant CV Excerpts (RAG)
{cv_context}

## Full CV Text
{cv_full_text}

Extract skills/requirements, compute an honest fit score with explanation, and identify skill gaps."""


def get_analysis_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [("system", ANALYSIS_SYSTEM), ("human", ANALYSIS_USER)]
    )


# ---------------------------------------------------------------------------
# Resume tailoring
# ---------------------------------------------------------------------------

TAILORING_SYSTEM = f"""You are an expert resume writer for students and early-career candidates.
{GROUNDING_RULES}
6. Rewrite exactly 5 bullets that best match this job — each must map to a REAL bullet or experience in the CV.
7. For each bullet provide: original_bullet, revised_bullet, section (Experience/Projects/Skills/Education/Other), reason_for_change.
8. original_bullet must quote or closely paraphrase text from the CV — never invent experience.
9. fit_score must be honest (0–100) with a clear 2–3 sentence explanation."""

TAILORING_USER = """Tailor this candidate's resume content for the target role.

## Company / Role
{company_name} — {job_title}

## Job Description
{job_description}

## Required Skills (extracted)
{required_skills}

## Relevant CV Excerpts (RAG)
{cv_context}

## Full CV Text
{cv_full_text}

Compare CV skills/projects against the JD. Identify matching, missing, and weak skills.
Produce a tailored summary and exactly 5 bullet improvements.
Each improved_bullets entry must include original_bullet, revised_bullet, section, and reason_for_change."""


def get_tailoring_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [("system", TAILORING_SYSTEM), ("human", TAILORING_USER)]
    )


# ---------------------------------------------------------------------------
# Cover letter
# ---------------------------------------------------------------------------

COVER_LETTER_SYSTEM = f"""You are an expert cover letter writer for internship and entry-level roles.
{GROUNDING_RULES}
6. Keep tone professional, warm, and concise.
7. Reference specific CV experiences that match the job requirements.
8. Write each cover letter section as a separate short paragraph — not one large block."""

COVER_LETTER_USER = """Write application materials for this candidate.

## Company / Role
{company_name} — {job_title}

## Job Description
{job_description}

## Tailored Resume Summary
{tailored_summary}

## Tailored Bullet Points
{tailored_bullets}

## Full CV Text
{cv_full_text}

Return:
1. email_message — short email to attach the CV (~100-150 words)
2. sections — structured cover letter with these fields:
   - greeting (e.g. Dear Hiring Manager,)
   - introduction (1-2 sentences: who you are + role applying for)
   - why_fit (2-3 sentences: why you fit, based on CV evidence)
   - relevant_skills_projects (2-4 sentences: specific skills/projects from CV)
   - closing (1-2 sentences: interest + availability)
   - sign_off (e.g. Sincerely, followed by name placeholder)"""


def get_cover_letter_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [("system", COVER_LETTER_SYSTEM), ("human", COVER_LETTER_USER)]
    )


# ---------------------------------------------------------------------------
# Interview preparation
# ---------------------------------------------------------------------------

INTERVIEW_SYSTEM = f"""You are an interview coach for students and entry-level candidates.
{GROUNDING_RULES}
6. suggested_answer must draw on specific CV projects, coursework, or experience.
7. Provide 10-12 questions total with a mix of technical, behavioral, and role questions.
8. question_type MUST be exactly one of these three strings — no other values allowed:
   - technical
   - behavioral
   - role
   Do NOT use "role-specific", "general", "soft-skill", or any other label."""

INTERVIEW_USER = """Prepare interview Q&A for this candidate.

## Company / Role
{company_name} — {job_title}

## Job Description
{job_description}

## Required Skills
{required_skills}

## Relevant CV Excerpts
{cv_context}

## Full CV Text
{cv_full_text}

Generate 10-12 interview questions with suggested answers grounded in the CV.
For each question set question_type to exactly "technical", "behavioral", or "role" — no other values."""


def get_interview_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [("system", INTERVIEW_SYSTEM), ("human", INTERVIEW_USER)]
    )
