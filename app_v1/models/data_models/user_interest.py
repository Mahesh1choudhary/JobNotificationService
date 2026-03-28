from pydantic import BaseModel


class UserInterest(BaseModel):
    role_name:str
    job_locations: list[str]
    company_names:list[str]

