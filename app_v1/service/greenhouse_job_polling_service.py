import asyncio
import json
import os
import time
from html import unescape
from pathlib import Path
from typing import Any

import requests

from app_v1.commons.service_logger import setup_logger
from app_v1.database.repository.job_repository import JobRepository
from app_v1.models.request_models.job_creation_request import JobCreationRequest

logger = setup_logger()

GH_JOBS_URL = "https://boards-api.greenhouse.io/v1/boards/{companyName}/jobs?content=true"
DEFAULT_COMPRESSED_PATH = Path(__file__).resolve().parent.parent / "config" / "greenhouse_clients_compressed.json"
DEFAULT_WHITELIST_PATH = Path(__file__).resolve().parent.parent / "config" / "whitelist_companies.json"


class GreenhouseJobPollingService:
    """
    Loads board tokens from greenhouse_clients_compressed.json (`data`: list of Greenhouse board slugs),
    keeps those present in whitelist_companies.json, fetches each board's public jobs API,
    and inserts that company's jobs right after each response.
    """

    def __init__(
        self,
        job_repository: JobRepository,
        compressed_json_path: Path | str | None = None,
        *,
        whitelist_json_path: Path | str | None = None,
        http_timeout: int = 10,
        poll_interval_seconds: float = 30.0,
        max_retries: int = 3,
    ):
        self._job_repository = job_repository
        self._compressed_path = Path(compressed_json_path or DEFAULT_COMPRESSED_PATH)
        self._whitelist_path = Path(whitelist_json_path or DEFAULT_WHITELIST_PATH)
        self._http_timeout = http_timeout
        self._poll_interval_seconds = poll_interval_seconds
        self._max_retries = max_retries

    def _load_whitelist_tokens(self) -> set[str]:
        if not self._whitelist_path.is_file():
            logger.error("Whitelist JSON not found: %s", self._whitelist_path)
            return set()
        with open(self._whitelist_path, encoding="utf-8") as f:
            obj = json.load(f)
        raw = obj.get("companies")
        if not isinstance(raw, list):
            logger.error("Whitelist JSON must contain a 'companies' array: %s", self._whitelist_path)
            return set()
        return {str(name).strip().lower() for name in raw if str(name).strip()}

    def _load_board_tokens(self) -> list[str]:
        if not self._compressed_path.is_file():
            logger.error("Greenhouse compressed JSON not found: %s", self._compressed_path)
            return []
        with open(self._compressed_path, encoding="utf-8") as f:
            obj = json.load(f)
        raw = obj.get("data")
        if not isinstance(raw, list):
            logger.error(
                "Greenhouse compressed JSON must have a 'data' array of board tokens: %s",
                self._compressed_path,
            )
            return []
        tokens: set[str] = set()
        for item in raw:
            if not isinstance(item, str):
                continue
            t = item.strip().lower()
            if t:
                tokens.add(t)
        whitelist = self._load_whitelist_tokens()
        if not whitelist:
            logger.warning("Whitelist is empty or invalid; skipping poll cycle")
            return []
        tokens = {t for t in tokens if t in whitelist}
        return sorted(tokens)

    def _fetch_jobs_payload(self, board_token: str) -> dict[str, Any] | None:
        url = GH_JOBS_URL.format(companyName=board_token)
        for attempt in range(self._max_retries):
            try:
                resp = requests.get(url, timeout=self._http_timeout)
                if resp.status_code == 200:
                    logger.debug("Retrieved board for token %s", board_token)
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

    def _rows_for_board(self, board_token: str, payload: dict[str, Any]) -> list[JobCreationRequest]:
        rows: list[JobCreationRequest] = []
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
                JobCreationRequest(
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
        total_submitted = 0
        for token in tokens:
            payload = await asyncio.to_thread(self._fetch_jobs_payload, token)
            if not payload:
                continue
            api_jobs = len(payload.get("jobs", []))
            rows = self._rows_for_board(token, payload)
            if not rows:
                continue
            n = await self._job_repository.insert_jobs_ignore_duplicates(rows)
            total_submitted += n
            logger.info(
                "Greenhouse poll company=%s: inserted batch of %s job rows (submitted to DB)",
                token,
                n,
            )
        logger.info(
            "Poll cycle finished: %s job rows submitted for insert across all companies",
            total_submitted,
        )

    async def run_forever(self) -> None:
        while True:
            try:
                await self.poll_once()
            except Exception:
                logger.exception("Greenhouse poll cycle failed")
            await asyncio.sleep(self._poll_interval_seconds)


def polling_enabled_from_env() -> bool:
    return os.getenv("GREENHOUSE_POLLING_ENABLED", "").strip().lower() in ("1", "true", "yes", "on")


def poll_interval_from_env(default: float = 360.0) -> float:
    raw = os.getenv("GREENHOUSE_POLL_INTERVAL_SECONDS")
    if not raw:
        return default
    try:
        return max(30.0, float(raw))
    except ValueError:
        return default
