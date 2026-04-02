from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class Company(BaseModel):
    company_id: Optional[int]
    company_name: str
    job_list_fetch_url: str
    created_at: Optional[datetime]