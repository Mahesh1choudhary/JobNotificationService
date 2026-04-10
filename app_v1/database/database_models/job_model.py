import hashlib
from datetime import datetime
from enum import StrEnum, Enum

from pydantic import BaseModel


class JobProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    SKIPPED = "skipped"

class Job(BaseModel):
    id: int
    job_company_id: int
    job_link: str
    job_description: str | None
    job_description_hash: str
    created_at: datetime | None
    job_processing_status: JobProcessingStatus
