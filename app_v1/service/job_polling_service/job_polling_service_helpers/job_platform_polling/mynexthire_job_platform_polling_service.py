import asyncio
from typing import List

import httpx

from app_v1.commons.service_logger import setup_logger
from app_v1.commons.time_utils import current_time_in_utc
from app_v1.database.database_models.company_job_source_model import CompanyJobSourceModel, FetchConfig, \
    FetchRequestConfig
from app_v1.models.request_models.job_creation_request import JobCreationRequest
from app_v1.service.job_polling_service.job_polling_service_helpers.job_platform_polling.base_job_platform_polling_service import \
    JobPlatformPollingService

logger = setup_logger()
class MynexthireJobPlatformPollingService(JobPlatformPollingService):

    async def fetch_job_data_for_company(self, company_job_source:CompanyJobSourceModel) -> List[JobCreationRequest]:
        try:
            logger.info(f"[{self.__class__.__name__}]-[{self.fetch_job_data_for_company.__name__}]: fetching jobs for company_job_source: {company_job_source}")
            fetch_config:FetchConfig = company_job_source.fetch_config
            if fetch_config is None:
                logger.warning(f"fetch_config not set for company_id: {company_job_source.company_id}")
                return []

            all_jobs_fetch: FetchRequestConfig = fetch_config.all_jobs_fetch

            #fethcing company jobs data
            #TODO: need to add retries
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=all_jobs_fetch.method,
                    url=all_jobs_fetch.url,
                    headers=all_jobs_fetch.headers,
                    json=all_jobs_fetch.payload,
                )

            company_job_source.last_fetched_at = current_time_in_utc()

            company_jobs_data = response.json().get("reqDetailsBOList", None)
            if company_jobs_data is None:
                logger.warning(f"company_jobs_data is empty for company_id: {company_job_source.id}")
                return []

            tasks = [self.process_job_data(job_data, company_job_source) for job_data in company_jobs_data]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            job_creation_requests = [req for req in results if req is not None]
            logger.info(f"[{self.__class__.__name__}]-[{self.fetch_job_data_for_company.__name__}]: fetched {len(job_creation_requests)} valid jobs for company_job_source: {company_job_source}")
            return job_creation_requests
        except Exception as exc:
            logger.error(f"[{self.__class__.__name__}]-[{self.fetch_job_data_for_company.__name__}]: error fetching jobs for company_job_source: {company_job_source}", exc_info=exc)
            return []


    async def process_job_data(self, job_data: dict, company_job_source:CompanyJobSourceModel) -> JobCreationRequest:
        try:
            logger.info(f"[{self.__class__.__name__}]-[{self.process_job_data.__name__}]: processing job for company_id: {company_job_source.company_id}")
            company_specific_job_id = job_data.get("reqId", None)
            # TODO: this is compulsory as of now -> as we define uniqueness of job based on this only in database
            #TODO: will ignore jobs wihtout internal job id for now
            if company_specific_job_id is None:
                logger.info(f"[{self.__class__.__name__}]-[{self.process_job_data.__name__}]: company_specific_job_id is None for job for company_id: {company_job_source.company_id}")
                return None

            job_link = None #TODO: need to check how to fill this for mynexthire platform
            job_description = f"job location data : {job_data.get('locationList', None)};" + f"department data : {job_data.get('buName', None)};"

            #TODO: need to do processing on job_content
            job_description = job_description + f"job content data : {job_data.get('jdDisplay', None)}"
            company_specific_job_id = str(company_specific_job_id)
            return JobCreationRequest(job_company_id=company_job_source.company_id, job_internal_id=company_specific_job_id, job_link=job_link, job_description=job_description)
        except Exception as exc:
            logger.error(f"[{self.__class__.__name__}]-[{self.process_job_data.__name__}]: Error processing job for company_id:{company_job_source.company_id}", exc_info=True)
            return None








