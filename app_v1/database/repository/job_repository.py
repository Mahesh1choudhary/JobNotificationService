from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence

from app_v1.commons.service_logger import setup_logger
from app_v1.database.database_client import PostgresSQLDatabaseClient
from app_v1.database.database_models.job_model import compute_hash

logger = setup_logger()


def _utc_now_naive() -> datetime:
    """UTC wall time without tzinfo; asyncpg expects this for TIMESTAMP WITHOUT TIME ZONE."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


@dataclass(frozen=True)
class JobInsertRow:
    company: str
    job_link: str
    job_id: str | None
    job_description: str | None


@dataclass(frozen=True)
class JobRow:
    id: int
    company: str
    job_link: str
    job_id: str | None
    job_description: str | None
    description_hash: str
    created_at: datetime | None
    status: str


class JobRepository:
    """Persists Greenhouse (and other) job rows into the `jobs` table (see JobModel)."""

    def __init__(self, database_client: PostgresSQLDatabaseClient):
        self._database_client = database_client

    async def insert_jobs_ignore_duplicates(self, rows: Sequence[JobInsertRow]) -> int:
        """Insert rows; duplicates (same company, job_link, description_hash) are skipped. Returns rows submitted."""
        if not rows:
            return 0
        now = _utc_now_naive()
        args_list = []
        for r in rows:
            desc = r.job_description or ""
            h = compute_hash(desc)
            args_list.append((r.company, r.job_link, r.job_id, r.job_description, h, now, "pending"))

        query = """
        INSERT INTO jobs (company, job_link, job_id, job_description, description_hash, created_at, status)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (company, job_link, description_hash) DO NOTHING
        """
        try:
            await self._database_client.executemany(query, args_list)
        except Exception:
            logger.error("Database error in insert_jobs_ignore_duplicates", exc_info=True)
            raise
        return len(args_list)

    async def list_pending(self, *, limit: int = 1000, offset: int = 0) -> list[JobRow]:
        query = """
        SELECT id, company, job_link, job_id, job_description, description_hash, created_at, status
        FROM jobs
        WHERE status = 'pending'
        ORDER BY created_at ASC, id ASC
        LIMIT $1 OFFSET $2
        """
        try:
            rows = await self._database_client.fetch(query, limit, offset)
        except Exception:
            logger.error("Database error in list_pending", exc_info=True)
            raise
        return [JobRow(**dict(r)) for r in rows]

    async def mark_sent_by_id(self, job_id: int) -> bool:
        """Set status='sent' for a specific row id. Returns True if a row was updated."""
        query = "UPDATE jobs SET status = 'sent' WHERE id = $1"
        try:
            result = await self._database_client.execute(query, job_id)
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
        h = compute_hash(job_description or "")
        query = """
        UPDATE jobs
        SET status = 'sent'
        WHERE company = $1 AND job_link = $2 AND description_hash = $3
        """
        try:
            result = await self._database_client.execute(query, company, job_link, h)
        except Exception:
            logger.error(
                "Database error in mark_sent_by_unique_key company=%s job_link=%s",
                company,
                job_link,
                exc_info=True,
            )
            raise
        return str(result).strip().upper().endswith(" 1")
