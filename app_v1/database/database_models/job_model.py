import hashlib
from datetime import datetime

from pydantic import BaseModel


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
    status: str
