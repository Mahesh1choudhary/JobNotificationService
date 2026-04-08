import asyncio
import time
from datetime import datetime, timezone
from typing import List

from app_v1.commons.service_logger import setup_logger
from app_v1.database import database_client
from app_v1.database.database_client import BaseDatabaseClient
from app_v1.database.database_config import DatabaseConfigFactory
from app_v1.database.database_manager import DatabaseManager
from app_v1.database.database_models.company_job_source_model import CompanyJobSourceModel
from app_v1.database.repository.companies_job_sources_repository import CompaniesJobSourcesRepository
from app_v1.service.job_polling_service.job_polling_service_helpers.job_platform_polling.base_job_platform_polling_service import \
    JobPlatformPollingService
from app_v1.service.job_polling_service.job_polling_service_helpers.job_platform_polling_service_factory import \
    JobPlatformPollingServiceFactory

logger = setup_logger()

class JobPollingService():

    def __init__(self, database_client:BaseDatabaseClient):
        self._companies_job_sources_repository = CompaniesJobSourcesRepository(database_client)
        self._next_fetch_gap_seconds= 5*60 # 5 minutes gap between fetching same company data


    async def _poll_single_company_for_jobs(self, job_company_job_source:CompanyJobSourceModel):
        fetch_job_list_url = job_company_job_source.fetch_job_list_url
        if fetch_job_list_url is None:
            logger.error(f"fetch_job_list_url is empty for company_id: {job_company_job_source.company_id}")
            return
        job_platform_name = job_company_job_source.platform_name
        if job_platform_name is None:
            logger.error(f"job_platform_name is empty for company_id: {job_company_job_source.company_id}")

        last_fetched_at:datetime = job_company_job_source.last_fetched_at
        if last_fetched_at is not None:
            #TODO: check time zone here, last fetched at should also be in same time zone
            #TODO: currently limited is same for all, in future should be different fro each platform if needed
            time_after_last_fetched_seconds = (datetime.now(timezone.utc) - last_fetched_at).total_seconds()
            time_to_wait_seconds = self._next_fetch_gap_seconds - time_after_last_fetched_seconds
            if time_to_wait_seconds > 0:
                await asyncio.sleep(time_to_wait_seconds)

        job_platform_polling_service:JobPlatformPollingService = JobPlatformPollingServiceFactory.get_job_platform_polling_service(job_platform_name)
        if job_platform_polling_service is None:
            return
        await job_platform_polling_service.fetch_and_ingest_job_data_for_company(job_company_job_source)


    async def start_polling(self):
        logger.info(f"Starting the polling")
        while True:
            try:
                total_entries = await self._companies_job_sources_repository.get_total_entries_count()
                if total_entries == 0:
                    logger.warning("no entries to poll on")

                batch_size = 5 #TODO: should be config driven
                for offset in range(0, total_entries, batch_size):
                    batch_job_sources:List[CompanyJobSourceModel] = await self._companies_job_sources_repository.get_companies_job_source_data(
                        offset=offset,
                        limit=batch_size
                    )

                    tasks = [self._poll_single_company_for_jobs(company_job_source_data) for company_job_source_data in batch_job_sources]
                    await asyncio.gather(*tasks)
            except Exception as exc:
                logger.error(f"Exception occurred in start_polling: {exc}")

