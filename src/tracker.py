"""
Application tracker — Session-isolated storage for full privacy in multi-user deployments.
"""

from typing import Optional
from src.models import ApplicationRecord, ApplicationStatus


class SessionTracker:
    """
    Manages application records scoped strictly to the current user's session.
    Ensures that when the app is deployed publicly, no visitor can see another visitor's
    CVs, jobs, cover letters, or saved applications.
    """

    def __init__(self, session_store: dict):
        self.store = session_store

    def create(
        self,
        company_name: str,
        job_title: str,
        job_description_text: str,
        cv_text: Optional[str] = None,
    ) -> ApplicationRecord:
        """Create a new application with status 'planned'."""
        record = ApplicationRecord(
            company_name=company_name.strip(),
            job_title=job_title.strip(),
            job_description_text=job_description_text.strip(),
            cv_text=cv_text,
        )
        return self.save(record)

    def save(self, record: ApplicationRecord) -> ApplicationRecord:
        """Insert or update a record in the user's private session."""
        self.store[record.application_id] = record
        return record

    def get(self, application_id: str) -> Optional[ApplicationRecord]:
        """Fetch one application by ID from the private session."""
        return self.store.get(application_id)

    def list_all(self) -> list[ApplicationRecord]:
        """List all applications for this session, newest first."""
        records = list(self.store.values())
        records.sort(key=lambda r: r.date_created, reverse=True)
        return records

    def set_status(self, application_id: str, status: ApplicationStatus) -> Optional[ApplicationRecord]:
        """Update application pipeline status."""
        record = self.store.get(application_id)
        if record:
            record.status = status
            return record
        return None

    def delete(self, application_id: str) -> bool:
        """Permanently delete an application from the session."""
        return bool(self.store.pop(application_id, None))


# Alias for backward compatibility
ApplicationTracker = SessionTracker
