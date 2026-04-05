from pydantic import BaseModel


class JobCompanyNameVector(BaseModel):
    company_name: str #TODO: should be same as column names in database- we are usign in that way
    description: str # other company names, etc -> amazon, aws or google, google deepmind, etc