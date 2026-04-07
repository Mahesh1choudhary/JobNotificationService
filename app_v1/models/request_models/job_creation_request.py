from pydantic import BaseModel


class JobCreationRequest(BaseModel):
    company: str
    job_link: str
    job_id: str | None
    job_description: str | None
