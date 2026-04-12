from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class FetchRequestConfig(BaseModel):
    method: str = Field(default="GET")
    url: str
    headers : Optional[Dict[str,str]] = Field(default_factory=dict)
    payload: Optional[Dict[str,Any]] = None



class FetchConfig(BaseModel):
    all_jobs_fetch: FetchRequestConfig
    individual_job_fetch: Optional[FetchRequestConfig] = None



#TODO: using same object at multiple places with selected parameters, need to update
class CompanyJobSourceModel(BaseModel):
    id: Optional[int] = None
    company_id: Optional[int]= None
    company_name: Optional[str] = None
    platform_id: Optional[int] = None
    platform_name: Optional[str] = None
    fetch_config: Optional[FetchConfig] = None
    last_fetched_at: Optional[datetime] = None