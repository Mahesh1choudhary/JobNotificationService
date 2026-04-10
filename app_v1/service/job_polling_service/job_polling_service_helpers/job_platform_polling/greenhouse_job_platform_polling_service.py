import asyncio
from datetime import datetime, timezone
from typing import List

import httpx
from sqlalchemy import true

from app_v1.commons.service_logger import setup_logger
from app_v1.database.database_models.company_job_source_model import CompanyJobSourceModel
from app_v1.database.repository.job_repository import JobRepository
from app_v1.models.request_models.job_creation_request import JobCreationRequest
from app_v1.service.job_polling_service.job_polling_service_helpers.job_platform_polling.base_job_platform_polling_service import JobPlatformPollingService

logger = setup_logger()
class GreenhouseJobPlatformPollingService(JobPlatformPollingService):

    async def fetch_job_data_for_company(self, company_job_source:CompanyJobSourceModel) -> List[JobCreationRequest]:
        try:
            fetch_job_list_url = company_job_source.fetch_job_list_url
            if fetch_job_list_url is None:
                logger.warning(f"fetch_job_url not set for company_id: {company_job_source.company_id}")
                return []

            #fethcing company jobs data
            #TODO: need to add retries
            async with httpx.AsyncClient() as client:
                response = await client.get(fetch_job_list_url)

            #TODO: need to check the timezone
            company_job_source.last_fetched_at = datetime.now(timezone.utc)

            company_jobs_data = response.json().get("jobs", None)
            if company_jobs_data is None:
                logger.warning(f"company_jobs_data is empty for company_id: {company_job_source.id}")
                return []

            tasks = [self._process_job_data(job_data, company_job_source.company_id) for job_data in company_jobs_data]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            job_creation_requests = [req for req in results if req is not None]
            return job_creation_requests
        except Exception as exc:
            logger.error(f"Error in {self.fetch_job_data_for_company.__name__}", exc_info=exc)
            return []



    async def _process_job_data(self, job_data: dict, job_company_id: int) -> JobCreationRequest:
        try:
            company_specific_job_id = job_data.get("internal_job_id", None)
            job_link = job_data.get("absolute_url", None)

            #TODO: need to do processing on job_content
            job_description = job_data.get("content")
            return JobCreationRequest(job_company_id=job_company_id, job_link=job_link, job_description=job_description)
        except Exception as exc:
            logger.error(f"Error in {self.process_job_data.__name__} for job_data:{job_data}", exc_info=True)
            return None







