import asyncio
from typing import List
from bs4 import BeautifulSoup
import json

import httpx

from app_v1.commons.concurrency_controller import AsyncConcurrencyController
from app_v1.commons.service_logger import setup_logger
from app_v1.commons.time_utils import current_time_in_utc
from app_v1.database.database_models.company_job_source_model import CompanyJobSourceModel, FetchConfig, \
    FetchRequestConfig
from app_v1.models.request_models.job_creation_request import JobCreationRequest
from app_v1.service.job_polling_service.job_polling_service_helpers.job_platform_polling.base_job_platform_polling_service import \
    JobPlatformPollingService

logger = setup_logger()

class RipplingJobPlatformPollingService(JobPlatformPollingService):
    def __init__(self):
        #TODO: rippling is blocking ip for too many calls. -> in future need to check in database and only fetch jobs that are not fetched yet or not present in database
        self.async_concurrency_controller =  AsyncConcurrencyController(1)
        self._process_job_data = self.async_concurrency_controller.limit_concurrency(self.process_job_data) # wrapped in concurrency controller



    async def fetch_job_data_for_company(self, company_job_source:CompanyJobSourceModel) -> List[JobCreationRequest]:
        try:
            logger.info(f"[{self.__class__.__name__}]-[{self.fetch_job_data_for_company.__name__}]: fetching jobs for company_job_source: {company_job_source}")
            fetch_config:FetchConfig = company_job_source.fetch_config

            if fetch_config is None:
                logger.warning(f"fetch_config not set for company_id: {company_job_source.company_id}")
                return []

            all_jobs_fetch: FetchRequestConfig = fetch_config.all_jobs_fetch
            if all_jobs_fetch is None:
                logger.warning(f"all_jobs_fetch not set for company_id: {company_job_source.company_id}")
                return []

            #fethcing company jobs data
            #TODO: need to add retries and timeouts
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=all_jobs_fetch.method,
                    url=all_jobs_fetch.url,
                    headers=all_jobs_fetch.headers,
                    json=all_jobs_fetch.payload,
                )

            company_job_source.last_fetched_at = current_time_in_utc()

            soup = BeautifulSoup(response.text, "lxml")
            script= soup.find("script", {"id": "__NEXT_DATA__"}).text.strip()
            val_json=json.loads(script)
            company_jobs_data = val_json["props"]["pageProps"]["jobs"]["items"]
            if company_jobs_data is None:
                logger.warning(f"company_jobs_data is empty for company_id: {company_job_source.id}")
                return []

            tasks = [self._process_job_data(job_data, company_job_source.company_id) for job_data in company_jobs_data]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            job_creation_requests = [req for req in results if req is not None]
            logger.info(f"[{self.__class__.__name__}]-[{self.fetch_job_data_for_company.__name__}]: fetched {len(job_creation_requests)} valid jobs for company_job_source: {company_job_source}")
            return job_creation_requests
        except Exception as exc:
            logger.error(f"[{self.__class__.__name__}]-[{self.fetch_job_data_for_company.__name__}]: error fetching jobs for company_job_source: {company_job_source}", exc_info=exc)
            return []



    async def process_job_data(self, job_data: dict, job_company_id: int) -> JobCreationRequest:
        try:
            logger.info(f"[{self.__class__.__name__}]-[{self._process_job_data.__name__}]: processing job for company_id: {job_company_id}")
            company_specific_job_id = job_data.get("id", None)
            # TODO: this is compulsory as of now -> as we define uniqueness of job based on this only in database
            #TODO: will ignore jobs wihtout internal job id for now
            if company_specific_job_id is None:
                logger.info(f"[{self.__class__.__name__}]-[{self._process_job_data.__name__}]: company_specific_job_id is None for job for company_id: {job_company_id}")
                return None

            job_link = job_data.get("url", None)

            #TODO: need to create a single function
            max_retries=5
            base_delay=1
            async with httpx.AsyncClient() as client:
                for attempt in range(max_retries):
                    try:
                        response = await client.request(
                            method="GET",
                            headers={
                                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                                "Accept": "application/json, text/plain, */*",
                                "Referer": "https://www.rippling.com/",
                            },
                            url=job_link,
                            timeout=httpx.Timeout(4.0, connect=2.0)
                        )

                        # If the server gives a 429 (Rate Limit) or 5xx (Server Error), we retry
                        if response.status_code in {429, 500, 502, 503, 504}:
                            response.raise_for_status()

                            # If successful (or a non-retryable error like 404), break the loop
                        break

                    except (httpx.ConnectTimeout, httpx.ReadError, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                        if attempt == max_retries - 1:
                            logger.error(f"Max retries reached for {job_link}. Final error: {exc}")
                            raise

                        # Exponential Backoff: 2s, 4s, 8s...
                        wait_time = base_delay  + attempt
                        logger.warning(f"Attempt {attempt + 1} failed. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)

            soup = BeautifulSoup(response.text, "lxml")
            script= soup.find("script", {"id": "__NEXT_DATA__"}).text.strip()
            val_json=json.loads(script)
            job_data = val_json["props"]["pageProps"]["apiData"]["jobPost"]


            job_description = f"job location data : {job_data.get('workLocations', None)};" + f"department data : {job_data.get('department', None)};"

            #TODO: need to do processing on job_content
            job_description = job_description + f"job content data : {job_data.get('description', None)}"
            company_specific_job_id = str(company_specific_job_id)
            return JobCreationRequest(job_company_id=job_company_id, job_internal_id=company_specific_job_id, job_link=job_link, job_description=job_description)
        except Exception as exc:
            logger.error(f"[{self.__class__.__name__}]-[{self._process_job_data.__name__}]: Error processing job for company_id:{job_company_id}", exc_info=True)
            return None







