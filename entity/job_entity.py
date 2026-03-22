from dataclasses import dataclass
from typing import Optional


@dataclass
class JobEntity:
    """Domain entity representing an outbox row for a job posting."""
    uuid: str
    job_company: str
    job_id: Optional[str]
    job_link: Optional[str]
    job_description: Optional[str]
    status: str  # CREATED | SENT | etc.
