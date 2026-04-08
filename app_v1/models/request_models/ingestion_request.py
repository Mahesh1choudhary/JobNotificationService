from typing import List, Any, Union
from enum import Enum

from pydantic import BaseModel

from app_v1.vector_data.job_company_name_namespace import JobCompanyNameNamespace
from app_v1.vector_data.job_location_namespace import JobLocationNamespace
from app_v1.vector_data.vector_data_models.job_company_name_vector import JobCompanyNameVector
from app_v1.vector_data.vector_data_models.job_location_vector import JobLocationVector


class NamespaceType(str, Enum):
    JOB_COMPANY_NAME_NAMESPACE = JobCompanyNameNamespace.get_namespace_name()
    JOB_LOCATION_NAMESPACE = JobLocationNamespace.get_namespace_name()


class IngestionRequest(BaseModel):
    namespace_type: NamespaceType
    data: List[Union[JobCompanyNameVector, JobLocationVector]]


class CompanyJobSourceIngestionRequest(BaseModel):
    company_name: str
    platform_name: str
    fetch_job_list_url: str
