from pydantic import BaseModel

from app_v1.models.data_models.job_tag_response import ExperienceLevel


class JobMatchCriteria(BaseModel):
    job_experience_level: ExperienceLevel
    job_location: str
    job_company_name: str
