"""
SQLite persistence for job application records.

Uses a single database file at data/applications.db.
JSON columns store lists and nested objects as text.
"""

import sqlite3
from contextlib import contextmanager
from typing import Optional

from src.models import ApplicationRecord, ApplicationStatus
from src.utils import DB_PATH, ensure_data_dir, from_json, to_json


def _init_db(conn: sqlite3.Connection) -> None:
    """Create the applications table if it does not exist."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
            application_id TEXT PRIMARY KEY,
            company_name TEXT NOT NULL,
            job_title TEXT NOT NULL,
            job_description_text TEXT NOT NULL,
            date_created TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'planned',
            cv_text TEXT,
            extracted_skills TEXT,
            extracted_requirements TEXT,
            matching_skills TEXT,
            missing_skills TEXT,
            weak_matches TEXT,
            fit_score INTEGER,
            fit_score_explanation TEXT,
            tailored_summary TEXT,
            tailored_resume_bullets TEXT,
            cover_letter TEXT,
            cover_letter_email TEXT,
            interview_questions_and_answers TEXT
        )
        """
    )
    conn.commit()
    _migrate(conn)


def _migrate(conn: sqlite3.Connection) -> None:
    """Add new columns to existing databases without breaking them."""
    existing = {row[1] for row in conn.execute("PRAGMA table_info(applications)")}
    new_columns = {
        "matching_skills": "TEXT",
        "missing_skills": "TEXT",
        "weak_matches": "TEXT",
    }
    for col, col_type in new_columns.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE applications ADD COLUMN {col} {col_type}")
    conn.commit()


@contextmanager
def get_connection():
    """Open a SQLite connection with row factory enabled."""
    ensure_data_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        _init_db(conn)
        yield conn
    finally:
        conn.close()


def _row_to_record(row: sqlite3.Row) -> ApplicationRecord:
    """Convert a database row into an ApplicationRecord."""
    return ApplicationRecord(
        application_id=row["application_id"],
        company_name=row["company_name"],
        job_title=row["job_title"],
        job_description_text=row["job_description_text"],
        date_created=row["date_created"],
        status=row["status"],
        cv_text=row["cv_text"],
        extracted_skills=from_json(row["extracted_skills"], []),
        extracted_requirements=from_json(row["extracted_requirements"], []),
        matching_skills=from_json(row["matching_skills"], []),
        missing_skills=from_json(row["missing_skills"], []),
        weak_matches=from_json(row["weak_matches"], []),
        fit_score=row["fit_score"],
        fit_score_explanation=row["fit_score_explanation"],
        tailored_summary=row["tailored_summary"],
        tailored_resume_bullets=from_json(row["tailored_resume_bullets"], []),
        cover_letter=row["cover_letter"],
        cover_letter_email=row["cover_letter_email"],
        interview_questions_and_answers=from_json(row["interview_questions_and_answers"], []),
    )


def save_application(record: ApplicationRecord) -> ApplicationRecord:
    """Insert or update an application record."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO applications (
                application_id, company_name, job_title, job_description_text,
                date_created, status, cv_text, extracted_skills, extracted_requirements,
                matching_skills, missing_skills, weak_matches,
                fit_score, fit_score_explanation, tailored_summary,
                tailored_resume_bullets, cover_letter, cover_letter_email,
                interview_questions_and_answers
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(application_id) DO UPDATE SET
                company_name=excluded.company_name,
                job_title=excluded.job_title,
                job_description_text=excluded.job_description_text,
                status=excluded.status,
                cv_text=excluded.cv_text,
                extracted_skills=excluded.extracted_skills,
                extracted_requirements=excluded.extracted_requirements,
                matching_skills=excluded.matching_skills,
                missing_skills=excluded.missing_skills,
                weak_matches=excluded.weak_matches,
                fit_score=excluded.fit_score,
                fit_score_explanation=excluded.fit_score_explanation,
                tailored_summary=excluded.tailored_summary,
                tailored_resume_bullets=excluded.tailored_resume_bullets,
                cover_letter=excluded.cover_letter,
                cover_letter_email=excluded.cover_letter_email,
                interview_questions_and_answers=excluded.interview_questions_and_answers
            """,
            (
                record.application_id,
                record.company_name,
                record.job_title,
                record.job_description_text,
                record.date_created,
                record.status,
                record.cv_text,
                to_json(record.extracted_skills),
                to_json(record.extracted_requirements),
                to_json(record.matching_skills),
                to_json(record.missing_skills),
                to_json(record.weak_matches),
                record.fit_score,
                record.fit_score_explanation,
                record.tailored_summary,
                to_json(record.tailored_resume_bullets),
                record.cover_letter,
                record.cover_letter_email,
                to_json(record.interview_questions_and_answers),
            ),
        )
        conn.commit()
    return record


def get_application(application_id: str) -> Optional[ApplicationRecord]:
    """Fetch a single application by ID."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM applications WHERE application_id = ?",
            (application_id,),
        ).fetchone()
    return _row_to_record(row) if row else None


def list_applications() -> list[ApplicationRecord]:
    """Return all applications, newest first."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM applications ORDER BY date_created DESC"
        ).fetchall()
    return [_row_to_record(row) for row in rows]


def delete_application(application_id: str) -> bool:
    """Delete an application by ID. Returns True if a row was removed."""
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM applications WHERE application_id = ?",
            (application_id,),
        )
        conn.commit()
        return cursor.rowcount > 0


def update_status(application_id: str, status: ApplicationStatus) -> Optional[ApplicationRecord]:
    """Update only the status field for an application."""
    record = get_application(application_id)
    if not record:
        return None
    record.status = status
    return save_application(record)
