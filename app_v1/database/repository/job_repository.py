from datetime import datetime, timezone
from typing import Sequence

from app_v1.commons.hash_function import compute_hash
from app_v1.commons.service_logger import setup_logger
from app_v1.database.database_client import PostgresSQLDatabaseClient, BaseDatabaseClient
from app_v1.database.database_models.job_model import Job, JobStatus
from app_v1.database.tables import DatabaseTables
from app_v1.models.request_models.job_creation_request import JobCreationRequest

logger = setup_logger()


def _utc_now_naive() -> datetime:
    #TODO: need to check here
    return datetime.now(timezone.utc).replace(tzinfo=None)


class JobRepository:
    def __init__(self, database_client: BaseDatabaseClient):
        self._database_client = database_client

    async def insert_jobs_ignore_duplicates(self, rows: Sequence[JobCreationRequest]) -> int:
        """Insert rows; duplicates (same company, job_link, description_hash) are skipped. Returns rows submitted."""
        if not rows:
            return 0
        now = _utc_now_naive()
        args_list = []
        for r in rows:
            desc = r.job_description or ""
            h = compute_hash(desc)
            args_list.append((r.company, r.job_link, r.job_id, r.job_description, h, now, JobStatus.PENDING.value))

        query = f"""
            INSERT INTO {DatabaseTables.JOB_TABLE.value} (company, job_link, job_id, job_description, description_hash, created_at, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (company, job_link, description_hash) DO NOTHING
        """
        try:
            await self._database_client.executemany(query, args_list)
        except Exception:
            logger.error("Database error in insert_jobs_ignore_duplicates", exc_info=True)
            raise
        return len(args_list)

    async def list_pending(self, *, limit: int = 1000, offset: int = 0) -> list[Job]:
        table = DatabaseTables.JOB_TABLE.value
        query = f"""
        SELECT id, company, job_link, job_id, job_description, description_hash, created_at, status
        FROM {table}
        WHERE status = $1
        ORDER BY created_at ASC, id ASC
        LIMIT $2 OFFSET $3
        """
        try:
            rows = await self._database_client.fetch(query, JobStatus.PENDING.value, limit, offset)
        except Exception:
            logger.error("Database error in list_pending", exc_info=True)
            raise
        return [Job(**dict(r)) for r in rows]

    async def mark_sent_by_id(self, job_id: int) -> bool:
        """Set status to done for a specific row id. Returns True if a row was updated."""
        #TODO: need to udpate here
        table = DatabaseTables.JOB_TABLE.value
        query = f"UPDATE {table} SET status = $2 WHERE id = $1"
        try:
            result = await self._database_client.execute(query, job_id, JobStatus.DONE.value)
        except Exception:
            logger.error("Database error in mark_sent_by_id id=%s", job_id, exc_info=True)
            raise
        # asyncpg returns strings like: "UPDATE 1"
        return str(result).strip().upper().endswith(" 1")

    async def mark_sent_by_unique_key(self, *, company: str, job_link: str, job_description: str | None) -> bool:
        """
        Convenience helper when you don't have the numeric id:
        updates the row identified by (company, job_link, description_hash).
        """
        #TODO: need to remove if not useful
        table = DatabaseTables.JOB_TABLE.value
        h = compute_hash(job_description or "")
        query = f"""
        UPDATE {table}
        SET status = $4
        WHERE company = $1 AND job_link = $2 AND description_hash = $3
        """
        try:
            result = await self._database_client.execute(query, company, job_link, h, JobStatus.DONE.value)
        except Exception:
            logger.error(
                "Database error in mark_sent_by_unique_key company=%s job_link=%s",
                company,
                job_link,
                exc_info=True,
            )
            raise
        return str(result).strip().upper().endswith(" 1")
