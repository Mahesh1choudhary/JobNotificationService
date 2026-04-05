from pydantic import BaseModel


class JobLocationVector(BaseModel):
    job_location: str
    description: str