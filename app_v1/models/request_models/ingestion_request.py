from typing import List, Any, Union
from enum import Enum

from pydantic import BaseModel

from app_v1.database.database_models.company_job_source_model import FetchConfig
from app_v1.vector_data.job_company_name_namespace import JobCompanyNameNamespace
from app_v1.vector_data.job_department_name_namespace import JobDepartmentNameNamespace
from app_v1.vector_data.job_location_namespace import JobLocationNamespace
from app_v1.vector_data.vector_data_models.job_company_name_vector import JobCompanyNameVector
from app_v1.vector_data.vector_data_models.job_department_name_vector import JobDepartmentNameVector
from app_v1.vector_data.vector_data_models.job_location_vector import JobLocationVector


class NamespaceType(str, Enum):
    JOB_COMPANY_NAME_NAMESPACE = JobCompanyNameNamespace.get_namespace_name()
    JOB_LOCATION_NAMESPACE = JobLocationNamespace.get_namespace_name()
    JOB_DEPARTMENT_NAME_NAMESPACE = JobDepartmentNameNamespace.get_namespace_name()


class IngestionRequest(BaseModel):
    namespace_type: NamespaceType
    data: List[Union[JobCompanyNameVector, JobLocationVector, JobDepartmentNameVector]]


class CompanyJobSourceIngestionRequest(BaseModel):
    company_name: str
    platform_name: str
    fetch_config: FetchConfig
