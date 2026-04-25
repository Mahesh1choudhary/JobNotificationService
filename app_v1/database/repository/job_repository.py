from datetime import datetime, timezone
from typing import Sequence, List

from app_v1.commons.hash_function import compute_hash
from app_v1.commons.service_logger import setup_logger
from app_v1.commons.time_utils import current_time_in_utc
from app_v1.database.database_client import BaseDatabaseClient
from app_v1.database.database_models.job_model import Job, JobProcessingStatus
from app_v1.database.tables import DatabaseTables
from app_v1.models.data_models.job_tag_response import JobTagResponse
from app_v1.models.request_models.job_creation_request import JobCreationRequest

logger = setup_logger()

class JobRepository:
    def __init__(self, database_client: BaseDatabaseClient):
        self._database_client = database_client

    async def insert_jobs_ignore_duplicates(self, rows: Sequence[JobCreationRequest]) -> None:
        """Insert rows; duplicates (same company, job_link, description_hash) are skipped."""

        query = f"""
            INSERT INTO {DatabaseTables.JOB_TABLE.value} (job_company_id, job_internal_id, job_link, job_description, job_description_hash, created_at, job_processing_status)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (job_company_id, job_internal_id) DO NOTHING
            RETURNING id, job_company_id, job_internal_id, job_link, job_description, job_description_hash, created_at, job_processing_status
        """
        try:
            if not rows:
                return []
            #TODO: need to check the time here
            current_time = current_time_in_utc()
            args_list = []
            for r in rows:
                job_description = r.job_description
                job_description_hash = compute_hash(job_description)
                args_list.append((r.job_company_id, r.job_internal_id, r.job_link, job_description, job_description_hash, current_time, JobProcessingStatus.PENDING.value))

            await self._database_client.executemany(query, args_list)
        except Exception:
            logger.error("Database error in insert_jobs_ignore_duplicates", exc_info=True)
            raise

    async def get_jobs_by_job_processing_status(self, job_processing_status: JobProcessingStatus, cutoff_timestamp:datetime, limit: int = 20, offset: int = 0) -> list[Job]:
        query = f"""
            SELECT id, job_company_id, job_internal_id, job_link, job_description, job_description_hash, created_at, job_processing_status
            FROM {DatabaseTables.JOB_TABLE.value}
            WHERE job_processing_status = $1 AND created_at > $2
            ORDER BY created_at DESC, id ASC
            LIMIT $3 OFFSET $4
        """
        try:
            rows = await self._database_client.fetch(query, job_processing_status, cutoff_timestamp, limit, offset)
            return [Job(**dict(r)) for r in rows]
        except Exception:
            logger.error(f"Database error in {self.get_jobs_by_job_processing_status.__name__}", exc_info=True)
            raise

    async def update_job_processing_status_by_id(self, job_ids: List[int], job_processing_status:JobProcessingStatus) -> None:
        """Set status to done for a given jobs rows"""
        query = f"""
            UPDATE {DatabaseTables.JOB_TABLE.value} SET job_processing_status = $2 WHERE id = ANY($1)
        """
        try:
            await self._database_client.execute(query, job_ids, job_processing_status)
        except Exception:
            logger.error(f"Database error in {self.update_job_processing_status_by_id.__name__} for job_ids: {job_ids}", exc_info=True)
            raise


    async def remove_old_jobs(self, cutoff_timestamp: datetime) -> None:
        query = f"""
            DELETE FROM {DatabaseTables.JOB_TABLE.value} 
            WHERE created_at < $1  
        """
        try:
            await self._database_client.execute(query, cutoff_timestamp)
        except Exception:
            logger.error(f"Database error in {self.remove_old_jobs.__name__}", exc_info=True)
            raise

    async def add_job_tag_responses(self, job_data_id:int, raw_job_tag_response:JobTagResponse, updated_job_tag_response:JobTagResponse) -> None:
        query = f"""
            UPDATE {DatabaseTables.JOB_TABLE.value}
            SET raw_job_tag_response= $2, updated_job_tag_response= $3
            WHERE id = $1
        """

        try:
            await self._database_client.execute(query, job_data_id, raw_job_tag_response.model_dump(), updated_job_tag_response.model_dump())
        except Exception:
            logger.error(f"Database error in {self.add_job_tag_responses.__name__}", exc_info=True)
            raise