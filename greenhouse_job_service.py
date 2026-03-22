import json
import logging
import uuid
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Protocol, Callable
import requests
import time
import os
from html import unescape

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# Domain entity representing the outbox row
@dataclass
class JobEntity:
    uuid: str
    job_company: str
    job_id: Optional[str]
    job_link: Optional[str]
    job_description: Optional[str]
    status: str  # CREATED | SENT | etc.


class JobRepository(Protocol):
    def save(self, entity: JobEntity) -> None:
        ...

    def list_by_status(self, status: str) -> List[JobEntity]:
        ...

    def update_status(self, uuid: str, new_status: str) -> None:
        ...


# Simple in-memory repository (suitable for tests / quick runs)
class InMemoryJobRepository:
    def __init__(self):
        self._store: Dict[str, JobEntity] = {}

    def save(self, entity: JobEntity) -> None:
        self._store[entity.uuid] = entity
        logger.debug("Saved job: %s", entity.uuid)

    def list_by_status(self, status: str) -> List[JobEntity]:
        return [e for e in self._store.values() if e.status == status]

    def update_status(self, uuid_: str, new_status: str) -> None:
        if uuid_ in self._store:
            ent = self._store[uuid_]
            ent.status = new_status
            self._store[uuid_] = ent
            logger.debug("Updated status %s -> %s", uuid_, new_status)
        else:
            logger.warning("Tried to update missing uuid: %s", uuid_)


# class DatabaseJobRepository:
#     def __init__(self, *args, **kwargs):
#         raise NotImplementedError("DatabaseJobRepository is not implemented yet.")


class GreenhouseJobService:
    GH_API_TEMPLATE = "https://boards-api.greenhouse.io/v1/boards/{companyName}/jobs?content=true"

    def __init__(self, repository: JobRepository, http_timeout: int = 10):
        self.repo = repository
        self.timeout = http_timeout

    @staticmethod
    def _company_from_domain(domain: str) -> str:
        # remove trailing .com if present, otherwise return domain's first label
        d = domain.strip().lower()
        if d.endswith(".com"):
            d = d[:-4]
        # remove any leading www. or path fragments if present
        d = d.split("/")[0]
        if d.startswith("www."):
            d = d[4:]
        # if still has dots, take the first label (e.g. careers.example -> careers)
        if "." in d:
            d = d.split(".")[0]
        return d

    def _fetch_jobs_for_company(self, company_name: str) -> Optional[Dict[str, Any]]:
        url = self.GH_API_TEMPLATE.format(companyName=company_name)
        logger.info("Requesting %s", url)
        # simple retry
        for attempt in range(3):
            try:
                resp = requests.get(url, timeout=self.timeout)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 404:
                    logger.info("No board found for %s (404).", company_name)
                    return None
                else:
                    logger.warning("Unexpected status %s for %s", resp.status_code, company_name)
            except requests.RequestException as exc:
                logger.warning("Request error for %s: %s (attempt %s)", company_name, exc, attempt + 1)
            time.sleep(1 + attempt)
        logger.error("Failed to fetch jobs for %s after retries.", company_name)
        return None

    def import_from_compressed(self, compressed_json_path: str) -> None:
        if not os.path.isfile(compressed_json_path):
            raise FileNotFoundError(compressed_json_path)
        with open(compressed_json_path, "r", encoding="utf-8") as f:
            obj = json.load(f)

        for rec in obj.get("data", []):
            domain = rec.get("domain")
            if not domain:
                logger.debug("Skipping record without domain: %s", rec.get("id"))
                continue
            company = self._company_from_domain(domain)
            payload = self._fetch_jobs_for_company(company)
            if not payload:
                continue
            jobs = payload.get("jobs", [])
            for job in jobs:
                # Prefer internal_job_id (Greenhouse internal id), then id, then requisition_id
                job_id = job.get("internal_job_id") or job.get("id") or job.get("requisition_id") or None
                # job link: prefer absolute_url, then url, then a constructed fallback
                job_link = job.get("absolute_url") or job.get("url")
                if not job_link and job_id:
                    # fallback to public boards URL (best-effort)
                    job_link = f"https://boards.greenhouse.io/{company}/jobs/{job_id}"
                
                # job description: prefer 'content' (HTML escaped), unescape entities
                raw_content = job.get("content")
                if isinstance(raw_content, str) and raw_content.strip():
                    job_description = unescape(raw_content)
                else:
                    # fallback: serialize job JSON
                    job_description = json.dumps(job, ensure_ascii=False)
 
                entity = JobEntity(
                    uuid=str(uuid.uuid4()),
                    job_company=company,
                    job_id=str(job_id) if job_id is not None else None,
                    job_link=job_link,
                    job_description=job_description,
                    status="CREATED"
                )
                self.repo.save(entity)
                logger.info("Imported job %s for company %s -> uuid=%s", entity.job_id, company, entity.uuid)

    def flush_outbox(self, publisher: Callable[[JobEntity], bool]) -> None:
        """
        publisher: callable that accepts JobEntity and returns True if published successfully.
        On success, status is updated to 'SENT'.
        """
        to_send = self.repo.list_by_status("CREATED")
        logger.info("Flushing %d outbox items", len(to_send))
        for ent in to_send:
            try:
                ok = publisher(ent)
            except Exception as exc:
                logger.exception("Publisher raised for %s: %s", ent.uuid, exc)
                ok = False
            if ok:
                self.repo.update_status(ent.uuid, "SENT")
                logger.info("Marked SENT: %s", ent.uuid)


# Example/pseudo-publisher (replace with real publish logic)
def example_publisher(job: JobEntity) -> bool:
    # This is where you'd send the job to another service (HTTP, message queue, etc.)
    logger.info("Publishing job uuid=%s company=%s job_id=%s", job.uuid, job.job_company, job.job_id)
    # Simulate success
    return True


# Simple CLI usage
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Import Greenhouse jobs into an outbox repository.")
    parser.add_argument("--input", default="greenhouse_clients_compressed.json", help="Compressed JSON file (relative).")
    parser.add_argument("--flush", action="store_true", help="Flush CREATED items using example publisher.")
    args = parser.parse_args()

    repo = InMemoryJobRepository()
    svc = GreenhouseJobService(repo)
    svc.import_from_compressed(args.input)

    if args.flush:
        svc.flush_outbox(example_publisher)
        logger.info("After flush, SENT count: %d", len(repo.list_by_status("SENT")))
