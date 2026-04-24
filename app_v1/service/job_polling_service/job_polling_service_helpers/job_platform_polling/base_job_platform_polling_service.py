from abc import ABC, abstractmethod
from typing import List

import httpx

from app_v1.commons.service_logger import setup_logger
from app_v1.database.database_models.company_job_source_model import CompanyJobSourceModel
from app_v1.models.request_models.job_creation_request import JobCreationRequest

logger = setup_logger()

class JobPlatformPollingService(ABC):

    @abstractmethod
    async def fetch_job_data_for_company(self, job_company_job_source:CompanyJobSourceModel) -> List[JobCreationRequest]:
        pass

    @abstractmethod
    async def process_job_data(self, job_data: dict, job_company_id: int):
        pass
