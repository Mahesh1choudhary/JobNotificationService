import logging
from entity.job_entity import JobEntity
from typing import List, Dict

logger = logging.getLogger(__name__)


class InMemoryJobRepository:
    """Simple in-memory repository (suitable for tests / quick runs)."""
    def __init__(self):
        self._store: Dict[str, JobEntity] = {}

    def save(self, entity: JobEntity) -> None:
        self._store[entity.composite_key] = entity
        logger.debug("Saved job: %s", entity.composite_key)

    def list_by_status(self, status: str) -> List[JobEntity]:
        return [e for e in self._store.values() if e.status == status]

    def update_status(self, uuid_: str, new_status: str) -> None:
        for composite_key, ent in self._store.items():
            if ent.uuid == uuid_:
                ent.status = new_status
                self._store[composite_key] = ent
                logger.debug("Updated status %s -> %s", uuid_, new_status)
                return
        logger.warning("Tried to update missing uuid: %s", uuid_)