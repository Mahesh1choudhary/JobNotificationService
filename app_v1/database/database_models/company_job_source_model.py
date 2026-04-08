from datetime import datetime
from pydantic import BaseModel
from typing import Optional

#TODO: using same object at multiple places with selected parameters, need to update
class CompanyJobSourceModel(BaseModel):
    id: Optional[int] = None
    company_id: Optional[int]= None
    company_name: Optional[str] = None
    platform_id: Optional[int] = None
    platform_name: Optional[str] = None
    fetch_job_list_url: Optional[str] = None
    last_fetched_at: Optional[datetime] = None