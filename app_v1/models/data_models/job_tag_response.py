from enum import Enum

from pydantic import BaseModel


class JobTagResponse(BaseModel):
    job_company_name: str # company to which this job belongs
    job_experience_level:ExperienceLevel # Whether Intern or full time
    job_location: str # job location -> Bangalore, New York , remote, etc
    job_department: str # Engineering, sales, finance, etc
    job_role_name: str # SDE1, Staff Engineer, customer success manager, etc
    job_summary: str # 4-5 lines about the job -> tech stack , year of experience etc.



class ExperienceLevel(str,Enum):
    INTERN = "Intern"
    FULL_TIME = "FullTime"

    @classmethod
    def _missing_(cls, value):
        value = value.lower()
        if "intern" in value:
            return cls.INTERN
        if "full" in value:
            return cls.FULL_TIME
        return None