from pydantic import BaseModel


class JobCreationRequest(BaseModel):
    job_company_id: int
    job_internal_id: int
    job_link: str | None
    job_description: str
