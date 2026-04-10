import asyncio
from datetime import datetime, timedelta
from typing import List

from app_v1.commons.service_logger import setup_logger
from app_v1.commons.time_utils import get_as_utc, utc_now
from app_v1.database.database_client import BaseDatabaseClient
from app_v1.database.database_models.company_job_source_model import CompanyJobSourceModel
from app_v1.database.database_models.job_model import Job, JobProcessingStatus
from app_v1.database.repository.companies_job_sources_repository import CompaniesJobSourcesRepository
from app_v1.database.repository.job_repository import JobRepository
from app_v1.models.request_models.job_creation_request import JobCreationRequest
from app_v1.service.job_notification_service import JobNotificationService
from app_v1.service.job_polling_service.job_polling_service_helpers.job_platform_polling.base_job_platform_polling_service import \
    JobPlatformPollingService
from app_v1.service.job_polling_service.job_polling_service_helpers.job_platform_polling_service_factory import \
    JobPlatformPollingServiceFactory

logger = setup_logger()

class JobPollingService():

    def __init__(self, database_client:BaseDatabaseClient):
        self._companies_job_sources_repository = CompaniesJobSourcesRepository(database_client)
        self._next_fetch_gap_seconds= 10*60 # 10 minutes gap between fetching same company data
        self._job_repository = JobRepository(database_client)
        self._job_notification_service = JobNotificationService(database_client)
        self._job_retention_period = timedelta(days=2) # 2 day old job will be removed from db whether processed or not


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
            last_fetched_at_utc = get_as_utc(last_fetched_at)
            time_after_last_fetched_seconds = (utc_now() - last_fetched_at_utc).total_seconds()
            time_to_wait_seconds = self._next_fetch_gap_seconds - time_after_last_fetched_seconds
            if time_to_wait_seconds > 0:
                await asyncio.sleep(time_to_wait_seconds)

        job_platform_polling_service:JobPlatformPollingService = JobPlatformPollingServiceFactory.get_job_platform_polling_service(job_platform_name)
        if job_platform_polling_service is None:
            return

        # last_fetched_a for in job_company_job_source object will be updated inside the method only
        job_creation_requests =  await job_platform_polling_service.fetch_job_data_for_company(job_company_job_source)
        await self._companies_job_sources_repository.update_company_job_source_last_fetched_at(job_company_job_source)

        await self.ingest_and_process_jobs(job_creation_requests)


    async def ingest_and_process_jobs(self, job_creation_requests: List[JobCreationRequest]) -> None:
        try:
            # adding new jobs as pending
            await self._job_repository.insert_jobs_ignore_duplicates(job_creation_requests)

            #fetching and processing any pending jobs
            #TODO: should fetch in batches - not all at once
            # fetching pending jobs that came after cut_off_timestamp
            cutoff_timestamp: datetime = utc_now() - self._job_retention_period
            all_pending_jobs: List[Job] = await self._job_repository.get_jobs_by_job_processing_status(JobProcessingStatus.PENDING, cutoff_timestamp, 5000,0)
            tasks = [self._job_notification_service.generate_tags_and_send_notifications(job) for job in all_pending_jobs]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            processed_job_ids= []
            skipped_job_ids = []
            for job, result in zip(all_pending_jobs, results):
                if isinstance(result, Exception):
                    logger.error(f"Job {job.id} failed: {result}", exc_info=True)
                elif result == JobProcessingStatus.PROCESSED:
                    processed_job_ids.append(job.id)
                elif result == JobProcessingStatus.SKIPPED:
                    skipped_job_ids.append(job.id)

            await self._job_repository.update_job_processing_status_by_id(processed_job_ids, JobProcessingStatus.PROCESSED)
            await self._job_repository.update_job_processing_status_by_id(skipped_job_ids, JobProcessingStatus.SKIPPED)

        except Exception as exc:
            logger.error(f"Error in {self.ingest_and_process_jobs.__name__}", exc_info=True)

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
                    await asyncio.gather(*tasks, return_exceptions=True)

                #TODO: cannot delete jobs as the next fetch will bring them again and will udpate in database- need to think of solution
                #cutoff_timestamp: datetime = utc_now() - self._job_retention_period
                #await self._job_repository.remove_old_jobs(cutoff_timestamp) # deleting jobs that came before cutoff_timestamp
            except Exception as exc:
                logger.error(f"Exception occurred in start_polling: {exc}")

