from enum import Enum
from pydantic import BaseModel


class JobType(str, Enum):
    INTERN = "Intern"
    FULL_TIME = "FullTime"
    CONTRACT = "Contract"
    FREELANCE = "Freelance"

    @classmethod
    def _missing_(cls, value):
        value = value.lower()
        if "intern" in value:
            return cls.INTERN
        if "full" in value:
            return cls.FULL_TIME
        if "contract" in value:
            return cls.CONTRACT
        if "freelance" in value:
            return cls.FREELANCE
        return None


class ExperienceLevel(str, Enum):
    ENTRY =  "[0,2)"
    JUNIOR = "[2-4)"
    MID = "[4-6)"
    SENIOR = "[6-10)"
    EXPERT = "10+"



class JobTagResponse(BaseModel):
    job_role_name: str # SDE1, Staff Engineer, customer success manager, etc
    job_company_name: str # company to which this job belongs
    job_type:JobType # Whether Intern or full time
    job_experience_level: ExperienceLevel # in number of years
    job_location: str # job location -> Bangalore, New York , remote, etc
    job_department: str # Engineering, sales, finance, etc
    job_summary: str # 4-5 lines about the job -> tech stack , year of experience etc.
