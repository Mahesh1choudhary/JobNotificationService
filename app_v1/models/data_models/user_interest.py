from pydantic import BaseModel


class UserInterest(BaseModel):
    role_name:str | None
    job_locations:str | None
    company_names:list[str]

