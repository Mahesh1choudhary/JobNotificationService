from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence

from app_v1.commons.service_logger import setup_logger
from app_v1.database.database_client import BaseDatabaseClient
from app_v1.database.database_models.job_model import compute_hash

logger = setup_logger()


@dataclass(frozen=True)
class JobInsertRow:
    company: str
    job_link: str
    job_id: str | None
    job_description: str | None


class JobRepository:
    """Persists Greenhouse (and other) job rows into the `jobs` table (see JobModel)."""

    def __init__(self, database_client: BaseDatabaseClient):
        self._database_client = database_client

    async def insert_jobs_ignore_duplicates(self, rows: Sequence[JobInsertRow]) -> int:
        """Insert rows; duplicates (same company, job_link, description_hash) are skipped. Returns rows submitted."""
        if not rows:
            return 0
        now = datetime.now(timezone.utc)
        args_list = []
        for r in rows:
            desc = r.job_description or ""
            h = compute_hash(desc)
            args_list.append((r.company, r.job_link, r.job_id, r.job_description, h, now))

        query = """
        INSERT INTO jobs (company, job_link, job_id, job_description, description_hash, created_at)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (company, job_link, description_hash) DO NOTHING
        """
        try:
            await self._database_client.executemany(query, args_list)
        except Exception:
            logger.error("Database error in insert_jobs_ignore_duplicates", exc_info=True)
            raise
        return len(args_list)
