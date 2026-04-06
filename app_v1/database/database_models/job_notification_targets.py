from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app_v1.models.data_models.job_tag_response import ExperienceLevel


class JobNotificationTarget(BaseModel):
    id: Optional[int]
    job_experience_level: ExperienceLevel
    job_location: str
    company_name: str
    user_ids: list[int]
    created_at: datetime