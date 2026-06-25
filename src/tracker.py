"""
Application tracker — high-level API over SQLite storage.

Use this module from the Streamlit app instead of calling storage directly.
"""

from typing import Optional

from src.models import ApplicationRecord, ApplicationStatus
from src.storage import (
    delete_application,
    get_application,
    list_applications,
    save_application,
    update_status,
)


class ApplicationTracker:
    """Manage job application records with create, read, update, delete."""

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
        return save_application(record)

    def save(self, record: ApplicationRecord) -> ApplicationRecord:
        """Insert or update a full application record."""
        return save_application(record)

    def get(self, application_id: str) -> Optional[ApplicationRecord]:
        """Fetch one application by ID."""
        return get_application(application_id)

    def list_all(self) -> list[ApplicationRecord]:
        """List all applications, newest first."""
        return list_applications()

    def set_status(self, application_id: str, status: ApplicationStatus) -> Optional[ApplicationRecord]:
        """Update application pipeline status."""
        return update_status(application_id, status)

    def delete(self, application_id: str) -> bool:
        """Permanently delete an application."""
        return delete_application(application_id)
