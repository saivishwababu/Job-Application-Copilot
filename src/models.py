"""
Pydantic models for structured LLM outputs and application records.
"""

from datetime import datetime
from typing import Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

ApplicationStatus = Literal["planned", "applied", "interview", "rejected", "offer"]
BulletSection = Literal["Experience", "Projects", "Skills", "Education", "Other"]
QuestionType = Literal["technical", "behavioral", "role"]


class JDExtraction(BaseModel):
    """Skills and requirements extracted from a job description."""

    required_skills: list[str] = Field(description="Technical and soft skills required or preferred")
    extracted_requirements: list[str] = Field(
        description="Key responsibilities, qualifications, and requirements from the JD"
    )


class FitAnalysis(BaseModel):
    """Fit score with explanation and skill gap analysis."""

    fit_score: int = Field(ge=0, le=100, description="Honest fit score 0-100")
    fit_score_explanation: str = Field(
        description="2-3 sentence explanation of why this score was assigned"
    )
    matching_skills: list[str] = Field(description="Skills from the JD demonstrated in the CV")
    missing_skills: list[str] = Field(description="Required skills or keywords weak or absent in CV")
    weak_matches: list[str] = Field(
        description="Skills partially present but need stronger evidence in the CV"
    )


class BulletImprovement(BaseModel):
    """One resume bullet rewrite with context."""

    original_bullet: str = Field(description="The original bullet from the CV, quoted or paraphrased")
    revised_bullet: str = Field(description="Improved bullet grounded in the same real experience")
    section: BulletSection = Field(
        description="CV section this bullet belongs to: Experience, Projects, Skills, Education, or Other"
    )
    reason_for_change: str = Field(
        description="Brief reason why this bullet was revised for the target role"
    )


class TailoringResult(BaseModel):
    """Tailored resume content grounded in the CV."""

    tailored_summary: str = Field(description="2-4 sentence resume summary for this role")
    improved_bullets: list[BulletImprovement] = Field(
        description="Exactly 5 bullet improvements with original, revision, section, and reason"
    )
    fit_analysis: FitAnalysis


class CoverLetterSections(BaseModel):
    """Structured cover letter sections."""

    greeting: str = Field(description="Opening greeting, e.g. Dear Hiring Manager,")
    introduction: str = Field(description="1-2 sentences: who you are and the role you are applying for")
    why_fit: str = Field(description="2-3 sentences: why you fit this role based on CV evidence")
    relevant_skills_projects: str = Field(
        description="2-4 sentences: specific skills and projects from the CV that match the JD"
    )
    closing: str = Field(description="1-2 sentences: express interest and availability")
    sign_off: str = Field(description="Professional sign-off, e.g. Sincerely,\\n[Your Name]")


class CoverLetterResult(BaseModel):
    """Short email and structured full cover letter."""

    email_message: str = Field(description="Short professional email application message")
    sections: CoverLetterSections

    @property
    def full_cover_letter(self) -> str:
        """Assemble sections into a neatly formatted cover letter."""
        s = self.sections
        return "\n\n".join(
            [
                s.greeting.strip(),
                s.introduction.strip(),
                s.why_fit.strip(),
                s.relevant_skills_projects.strip(),
                s.closing.strip(),
                s.sign_off.strip(),
            ]
        )


class InterviewQA(BaseModel):
    """A single interview question with a suggested grounded answer."""

    question: str
    suggested_answer: str = Field(
        description="Answer grounded in the candidate's CV and projects only"
    )
    question_type: QuestionType = Field(
        description="Category: technical, behavioral, or role"
    )


class InterviewQARaw(BaseModel):
    """Loose schema for LLM output — question_type is a string to avoid API validation errors."""

    question: str
    suggested_answer: str
    question_type: str = Field(
        description="Must be exactly one of these three values: technical, behavioral, role"
    )


class InterviewPrepRaw(BaseModel):
    """Raw interview prep from LLM before type normalization."""

    questions: list[InterviewQARaw] = Field(
        description="10-12 interview questions with suggested answers"
    )


class InterviewPrepResult(BaseModel):
    """Full interview preparation package."""

    questions: list[InterviewQA] = Field(
        description="10-12 interview questions with suggested answers"
    )


class ApplicationRecord(BaseModel):
    """Persistent application record stored in SQLite."""

    application_id: str = Field(default_factory=lambda: str(uuid4()))
    company_name: str
    job_title: str
    job_description_text: str
    date_created: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: ApplicationStatus = "planned"
    cv_text: Optional[str] = None
    extracted_skills: list[str] = Field(default_factory=list)
    extracted_requirements: list[str] = Field(default_factory=list)
    matching_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    weak_matches: list[str] = Field(default_factory=list)
    fit_score: Optional[int] = None
    fit_score_explanation: Optional[str] = None
    tailored_summary: Optional[str] = None
    tailored_resume_bullets: list[dict] = Field(default_factory=list)
    cover_letter: Optional[str] = None
    cover_letter_email: Optional[str] = None
    interview_questions_and_answers: list[dict] = Field(default_factory=list)

    def to_dict(self) -> dict:
        return self.model_dump()
