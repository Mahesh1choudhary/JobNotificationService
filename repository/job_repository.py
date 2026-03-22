import logging
from typing import List, Dict, Protocol

from entity.job_entity import JobEntity

logger = logging.getLogger(__name__)


class JobRepository(Protocol):
    """Abstract repository interface for job entities."""
    def save(self, entity: JobEntity) -> None:
        ...

    def list_by_status(self, status: str) -> List[JobEntity]:
        ...

    def update_status(self, uuid: str, new_status: str) -> None:
        ...
