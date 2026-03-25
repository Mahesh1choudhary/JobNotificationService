import asyncio
import json
import os
import time
from html import unescape
from pathlib import Path
from typing import Any

import requests

from app_v1.commons.service_logger import setup_logger
from app_v1.database.repository.job_repository import JobInsertRow, JobRepository

logger = setup_logger()

GH_JOBS_URL = "https://boards-api.greenhouse.io/v1/boards/{companyName}/jobs?content=true"
DEFAULT_COMPRESSED_PATH = Path(__file__).resolve().parent.parent / "resources" / "greenhouse_clients_compressed.json"


class GreenhouseJobPollingService:
    """
    Periodically loads board tokens from compressed Greenhouse client JSON (domain → slug),
    fetches public job listings, and stores rows via JobRepository.
    """

    def __init__(
        self,
        job_repository: JobRepository,
        compressed_json_path: Path | str | None = None,
        *,
        http_timeout: int = 10,
        poll_interval_seconds: float = 3600.0,
        max_retries: int = 3,
    ):
        self._job_repository = job_repository
        self._compressed_path = Path(compressed_json_path or DEFAULT_COMPRESSED_PATH)
        self._http_timeout = http_timeout
        self._poll_interval_seconds = poll_interval_seconds
        self._max_retries = max_retries

    @staticmethod
    def board_token_from_domain(domain: str) -> str:
        """Map a careers site domain to the Greenhouse boards API token (same rules as legacy importer)."""
        d = domain.strip().lower()
        if d.endswith(".com"):
            d = d[:-4]
        d = d.split("/")[0]
        if d.startswith("www."):
            d = d[4:]
        if "." in d:
            d = d.split(".")[0]
        return d

    def _load_board_tokens(self) -> list[str]:
        if not self._compressed_path.is_file():
            logger.error("Greenhouse compressed JSON not found: %s", self._compressed_path)
            return []
        with open(self._compressed_path, encoding="utf-8") as f:
            obj = json.load(f)
        tokens: set[str] = set()
        for rec in obj.get("data", []):
            domain = rec.get("domain")
            if not domain:
                continue
            tokens.add(self.board_token_from_domain(domain))
        return sorted(tokens)

    def _fetch_jobs_payload(self, board_token: str) -> dict[str, Any] | None:
        url = GH_JOBS_URL.format(companyName=board_token)
        for attempt in range(self._max_retries):
            try:
                resp = requests.get(url, timeout=self._http_timeout)
                if resp.status_code == 200:
                    return resp.json()
                if resp.status_code == 404:
                    logger.debug("No board for token %s (404)", board_token)
                    return None
                logger.warning("Unexpected status %s for %s", resp.status_code, board_token)
            except requests.RequestException as exc:
                logger.warning("Request error for %s: %s (attempt %s)", board_token, exc, attempt + 1)
            if attempt + 1 < self._max_retries:
                time.sleep(1 + attempt)
        logger.error("Failed to fetch jobs for %s after retries", board_token)
        return None

    def _rows_for_board(self, board_token: str, payload: dict[str, Any]) -> list[JobInsertRow]:
        rows: list[JobInsertRow] = []
        for job in payload.get("jobs", []):
            job_id = job.get("internal_job_id") or job.get("id") or job.get("requisition_id")
            job_link = job.get("absolute_url") or job.get("url")
            if not job_link:
                if job_id is not None:
                    job_link = f"https://boards.greenhouse.io/{board_token}/jobs/{job_id}"
                else:
                    continue
            raw_content = job.get("content")
            if isinstance(raw_content, str) and raw_content.strip():
                job_description = unescape(raw_content)
            else:
                job_description = json.dumps(job, ensure_ascii=False)
            rows.append(
                JobInsertRow(
                    company=board_token,
                    job_link=job_link,
                    job_id=str(job_id) if job_id is not None else None,
                    job_description=job_description,
                )
            )
        return rows

    async def poll_once(self) -> None:
        tokens = await asyncio.to_thread(self._load_board_tokens)
        if not tokens:
            logger.warning("No board tokens loaded; skip poll cycle")
            return
        all_rows: list[JobInsertRow] = []
        for token in tokens:
            payload = await asyncio.to_thread(self._fetch_jobs_payload, token)
            if not payload:
                continue
            all_rows.extend(self._rows_for_board(token, payload))
        if all_rows:
            n = await self._job_repository.insert_jobs_ignore_duplicates(all_rows)
            logger.info("Poll cycle: submitted %s job rows for insert", n)

    async def run_forever(self) -> None:
        while True:
            try:
                await self.poll_once()
            except Exception:
                logger.exception("Greenhouse poll cycle failed")
            await asyncio.sleep(self._poll_interval_seconds)


def polling_enabled_from_env() -> bool:
    return os.getenv("GREENHOUSE_POLLING_ENABLED", "").strip().lower() in ("1", "true", "yes", "on")


def poll_interval_from_env(default: float = 3600.0) -> float:
    raw = os.getenv("GREENHOUSE_POLL_INTERVAL_SECONDS")
    if not raw:
        return default
    try:
        return max(30.0, float(raw))
    except ValueError:
        return default
