from pydantic import BaseModel


class JobCompanyNameVector(BaseModel):
    company_name: str # should be same as column names in database- we are usign in that way
    alias: str # other company names, etc -> amazon, aws or google, google deepmind, etc