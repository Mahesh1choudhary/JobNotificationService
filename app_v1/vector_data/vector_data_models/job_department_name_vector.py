from pydantic import BaseModel


class JobDepartmentNameVector(BaseModel):
    department_name: str # name similar to database column names, so change accordingly
    description: str # other possible names for department