import asyncio
from datetime import datetime, timedelta
from typing import List

from app_v1.commons.service_logger import setup_logger
from app_v1.commons.time_utils import current_time_in_utc
from app_v1.config.config_keys import SAME_COMPANY_POLLING_GAP_IN_SECONDS, JOB_RETENTION_PERIOD_IN_DAYS, \
    COMPANY_BATCH_SIZE_FOR_POLLING, JOB_PROCESSING_BATCH_SIZE
from app_v1.config.config_loader import fetch_key_value
from app_v1.database.database_client import BaseDatabaseClient
from app_v1.database.database_models.company_job_source_model import CompanyJobSourceModel, FetchConfig
from app_v1.database.database_models.job_model import Job, JobProcessingStatus
from app_v1.database.repository.companies_job_sources_repository import CompaniesJobSourcesRepository
from app_v1.database.repository.job_repository import JobRepository
from app_v1.models.job_processing_item import JobProcessingItem
from app_v1.models.request_models.job_creation_request import JobCreationRequest
from app_v1.service.job_notification_service import JobNotificationService
from app_v1.service.job_polling_service.job_polling_service_helpers.job_platform_polling.base_job_platform_polling_service import \
    JobPlatformPollingService
from app_v1.service.job_polling_service.job_polling_service_helpers.job_platform_polling_service_factory import \
    JobPlatformPollingServiceFactory

logger = setup_logger()


class JobPollingService:

    def __init__(self, database_client: BaseDatabaseClient):
        self._companies_job_sources_repository = CompaniesJobSourcesRepository(database_client)
        self._next_fetch_gap_seconds = fetch_key_value(SAME_COMPANY_POLLING_GAP_IN_SECONDS, int)
        self._job_repository = JobRepository(database_client)
        self._job_notification_service = JobNotificationService(database_client)
        self._job_retention_period = timedelta(days= fetch_key_value(JOB_RETENTION_PERIOD_IN_DAYS, int)) # given days old job will not be processed if still unprocessed

    async def _poll_single_company_for_jobs(self, job_company_job_source:CompanyJobSourceModel) -> List[JobProcessingItem]:
        try:
            if job_company_job_source.company_id != 73:
                return []

            logger.info(f"[{self.__class__.__name__}]-[{self._poll_single_company_for_jobs.__name__}]: polling for job_company_source: {job_company_job_source}")

            fetch_config: FetchConfig = job_company_job_source.fetch_config
            if fetch_config is None:
                logger.warning(f"[{self.__class__.__name__}]-[{self._poll_single_company_for_jobs.__name__}]: fetch_config is empty for company_job_source: {job_company_job_source}")
                return []

            job_platform_name = job_company_job_source.platform_name
            if job_platform_name is None:
                logger.warning(f"[{self.__class__.__name__}]-[{self._poll_single_company_for_jobs.__name__}]: job_platform_name is empty for company_job_source: {job_company_job_source}")
                return []

            last_fetched_at: datetime = job_company_job_source.last_fetched_at
            if last_fetched_at is not None:
                #TODO: currently limiting is same for all, in future should be different for each platform if needed
                time_after_last_fetched_seconds = (current_time_in_utc() - last_fetched_at).total_seconds()
                time_to_wait_seconds = self._next_fetch_gap_seconds - time_after_last_fetched_seconds
                if time_to_wait_seconds > 0:
                    logger.info(f"[{self.__class__.__name__}]-[{self._poll_single_company_for_jobs.__name__}]: waiting for {time_to_wait_seconds} seconds before fetching job data for job_company_job_source: {job_company_job_source}")
                    await asyncio.sleep(time_to_wait_seconds)

            job_platform_polling_service: JobPlatformPollingService = JobPlatformPollingServiceFactory.get_job_platform_polling_service(job_platform_name)
            if job_platform_polling_service is None:
                logger.warning(f"[{self.__class__.__name__}]-[{self._poll_single_company_for_jobs.__name__}]: No job_platform_polling_service selected for company_job_source: {job_company_job_source}")
                return []

            raw_job_items = await job_platform_polling_service.fetch_job_data_for_company(job_company_job_source)
            await self._companies_job_sources_repository.update_company_job_source_last_fetched_at(job_company_job_source)

            logger.info(f"[{self.__class__.__name__}]-[{self._poll_single_company_for_jobs.__name__}]: got {len(raw_job_items)} raw items for company_job_source: {job_company_job_source}")
            return [JobProcessingItem(job_platform_polling_service= job_platform_polling_service, job_data_item = item, job_company_id= job_company_job_source.company_id) for item in raw_job_items]
        except Exception as exc:
            logger.error(f"[{self.__class__.__name__}]-[{self._poll_single_company_for_jobs.__name__}]: Error fetching raw job items for company_job_source: {job_company_job_source}", exc_info=True)
            return []

    async def ingest_and_process_jobs(self, job_creation_requests: List[JobCreationRequest]) -> None:
        try:
            logger.info(f"[{self.__class__.__name__}]-[{self.ingest_and_process_jobs.__name__}]: ingesting {len(job_creation_requests)} jobs")
            # adding new jobs as pending
            await self._job_repository.insert_jobs_ignore_duplicates(job_creation_requests)

            #fetching and processing any pending jobs
            #TODO: should fetch in batches - not all at once
            # fetching pending jobs that came after cut_off_timestamp
            cutoff_timestamp: datetime = current_time_in_utc() - self._job_retention_period
            all_pending_jobs: List[Job] = await self._job_repository.get_jobs_by_job_processing_status(JobProcessingStatus.PENDING, cutoff_timestamp, 5000, 0) # TODO: should fetch in batching
            logger.info(f"[{self.__class__.__name__}]-[{self.ingest_and_process_jobs.__name__}]: processing {len(all_pending_jobs)} jobs")
            tasks = [self._job_notification_service.generate_tags_and_send_notifications(job) for job in all_pending_jobs]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            processed_job_ids = []
            skipped_job_ids = []
            for job, result in zip(all_pending_jobs, results):
                if isinstance(result, Exception):
                    logger.error(f"[{self.__class__.__name__}]-[{self.ingest_and_process_jobs.__name__}]: Job {job.id} failed: {result}", exc_info=True)
                elif result == JobProcessingStatus.PROCESSED:
                    processed_job_ids.append(job.id)
                elif result == JobProcessingStatus.SKIPPED:
                    skipped_job_ids.append(job.id)
            await self._job_repository.update_job_processing_status_by_id(processed_job_ids, JobProcessingStatus.PROCESSED)
            await self._job_repository.update_job_processing_status_by_id(skipped_job_ids, JobProcessingStatus.SKIPPED)
            logger.info(f"""[{self.__class__.__name__}]-[{self.ingest_and_process_jobs.__name__}]: Out of {len(all_pending_jobs)} pending jobs; {len(processed_job_ids)} processed, {len(skipped_job_ids)} skipped, {len(all_pending_jobs) - len(processed_job_ids) - len(skipped_job_ids)} errored""")
        except Exception as exc:
            logger.error(f"[{self.__class__.__name__}]-[{self.ingest_and_process_jobs.__name__}]: Error", exc_info=True)

    async def start_polling(self):
        logger.info(f"[{self.__class__.__name__}]-[{self.start_polling.__name__}]: Starting the polling")
        while True:
            try:
                total_entries = await self._companies_job_sources_repository.get_total_entries_count()
                if total_entries == 0:
                    logger.warning(f"[{self.__class__.__name__}]-[{self.start_polling.__name__}]: no entries to poll for")
                    await asyncio.sleep(20)

                company_batch_size = fetch_key_value(COMPANY_BATCH_SIZE_FOR_POLLING, int)
                for offset in range(0, total_entries, company_batch_size):
                    batch_job_sources: List[CompanyJobSourceModel] = await self._companies_job_sources_repository.get_active_companies_job_source_data(
                        offset=offset,
                        limit=company_batch_size
                    )

                    # Phase 1: fetch raw job items from all companies in the batch concurrently
                    fetch_results = await asyncio.gather(
                        *[self._poll_single_company_for_jobs(company_job_source_data) for company_job_source_data in batch_job_sources],
                        return_exceptions=True
                    )

                    all_process_items: List[JobProcessingItem] = []
                    for result in fetch_results:
                        if not isinstance(result, Exception):
                            all_process_items.extend(result)

                    job_processing_batch_size = fetch_key_value(JOB_PROCESSING_BATCH_SIZE, int)
                    for job_offset in range(0, len(all_process_items), job_processing_batch_size):
                        job_creation_requests  = await asyncio.gather(
                            *[item.job_platform_polling_service.process_job_data(item.job_data_item, item.job_company_id)
                                                         for item in all_process_items[job_offset:job_offset + job_processing_batch_size]],
                            return_exceptions=True)

                        valid_job_creation_requests = []
                        for job_request in job_creation_requests:
                            if isinstance(job_request, Exception):
                                logger.error(f"Job processing failed for: {job_request}")
                            elif job_request is not None:
                                valid_job_creation_requests.append(job_request)

                        await self.ingest_and_process_jobs(valid_job_creation_requests)

                #TODO: cannot delete jobs as the next fetch will bring them again and will udpate in database- need to think of solution
                #cutoff_timestamp: datetime = utc_now() - self._job_retention_period
                #await self._job_repository.remove_old_jobs(cutoff_timestamp) # deleting jobs that came before cutoff_timestamp
            except Exception as exc:
                logger.error(f"[{self.__class__.__name__}]-[{self.start_polling.__name__}]: Exception occurred: {exc}")