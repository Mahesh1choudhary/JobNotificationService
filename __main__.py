import logging
import argparse

from repository.in_memory_job_repository import InMemoryJobRepository
from service.greenhouse_job_service import GreenhouseJobService, example_publisher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import Greenhouse jobs into an outbox repository.")
    parser.add_argument("--input", default="greenhouse_clients_compressed.json", help="Compressed JSON file (relative).")
    parser.add_argument("--flush", action="store_true", help="Flush CREATED items using example publisher.")
    args = parser.parse_args()

    repo = InMemoryJobRepository()
    svc = GreenhouseJobService(repo)
    svc.import_from_compressed(args.input)
    print(repo.list_by_status("CREATED"))

    if args.flush:
        svc.flush_outbox(example_publisher)
        logger.info("After flush, SENT count: %d", len(repo.list_by_status("SENT")))
