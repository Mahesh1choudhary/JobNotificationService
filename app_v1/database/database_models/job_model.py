import hashlib
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class JobStatus(StrEnum):
    """Persisted in the database as plain strings (e.g. VARCHAR/TEXT)."""

    PENDING = "pending"
    DONE = "done"


def compute_hash(description: str) -> str:
    return hashlib.sha256(description.encode("utf-8")).hexdigest()


class Job(BaseModel):
    id: int
    company: str
    job_link: str
    job_id: str | None
    job_description: str | None
    description_hash: str
    created_at: datetime | None
    status: JobStatus
