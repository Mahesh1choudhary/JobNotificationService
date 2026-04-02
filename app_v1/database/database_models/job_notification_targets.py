from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class JobNotificationTarget(BaseModel):
    id: Optional[int]
    job_role_name: str
    job_location: str
    company_name: str
    user_ids: list[int]
    created_at: datetime