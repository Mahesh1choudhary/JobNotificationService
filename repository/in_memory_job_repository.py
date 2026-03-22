class InMemoryJobRepository:
    """Simple in-memory repository (suitable for tests / quick runs)."""
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