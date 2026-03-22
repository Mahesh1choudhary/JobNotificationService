from dataclasses import dataclass, field
from typing import Optional
import hashlib


@dataclass
class JobEntity:
    """Domain entity representing an outbox row for a job posting."""
    uuid: str
    job_company: str
    job_id: Optional[str]
    job_link: Optional[str]
    job_description: Optional[str]
    status: str  # CREATED | SENT | etc.

    # computed MD5 hash of job_description (not provided at init)
    description_hash: str = field(init=False)

    def __post_init__(self):
        # compute MD5 of description (empty string if None)
        desc = (self.job_description or "").encode("utf-8")
        self.description_hash = hashlib.md5(desc).hexdigest()

    @property
    def composite_key(self) -> str:
        """Composite key: company | job_id (empty if None) | description_hash"""
        return f"{self.job_company}|{self.job_id or ''}|{self.description_hash}"
