from datetime import datetime
from pydantic import BaseModel


class Company(BaseModel):
    company_id: int
    company_name: str
    job_list_fetch_url: str
    created_at: datetime