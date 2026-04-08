from abc import ABC, abstractmethod

import httpx

from app_v1.commons.service_logger import setup_logger
from app_v1.database.database_models.company_job_source_model import CompanyJobSourceModel

logger = setup_logger()

class JobPlatformPollingService(ABC):

    @abstractmethod
    async def fetch_and_ingest_job_data_for_company(self, job_company_job_source:CompanyJobSourceModel):
        pass

