"""
Shared helpers for the Job Application Copilot app.
"""

import json
from pathlib import Path
from typing import Any

# Project root = parent of src/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "applications.db"


def ensure_data_dir() -> Path:
    """Create the data directory if it does not exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def to_json(value: Any) -> str:
    """Serialize a Python object to a JSON string for SQLite storage."""
    return json.dumps(value, ensure_ascii=False)


def from_json(value: str | None, default: Any = None) -> Any:
    """Deserialize a JSON string from SQLite; return default if empty."""
    if not value:
        return default if default is not None else []
    return json.loads(value)


def truncate(text: str, max_len: int = 120) -> str:
    """Truncate long text for display in lists."""
    text = text.strip().replace("\n", " ")
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def normalize_question_type(value: str) -> str:
    """
    Normalize LLM question_type values to exactly: technical, behavioral, or role.

    Groq structured output rejects invalid enum values at the API level,
    so we use a loose string schema first, then normalize here.
    """
    if not value:
        return "role"

    normalized = value.lower().strip().replace("_", "-").replace(" ", "-")

    aliases = {
        "role-specific": "role",
        "rolespecific": "role",
        "role-based": "role",
        "general": "role",
        "situational": "behavioral",
        "soft-skill": "behavioral",
        "soft-skills": "behavioral",
        "softskill": "behavioral",
        "culture": "behavioral",
        "tech": "technical",
        "coding": "technical",
    }

    if normalized in aliases:
        return aliases[normalized]
    if normalized in ("technical", "behavioral", "role"):
        return normalized
    if "technical" in normalized or "tech" in normalized:
        return "technical"
    if "behavior" in normalized:
        return "behavioral"
    return "role"


def bullets_to_storage(bullets: list) -> list[dict]:
    """Convert BulletImprovement objects or dicts to storable dicts."""
    result = []
    for item in bullets:
        if hasattr(item, "model_dump"):
            result.append(item.model_dump())
        elif isinstance(item, dict):
            result.append(item)
        elif isinstance(item, str):
            # Legacy plain-string bullets
            result.append(
                {
                    "original_bullet": "—",
                    "revised_bullet": item,
                    "section": "Other",
                    "reason_for_change": "Previously saved format",
                }
            )
    return result
