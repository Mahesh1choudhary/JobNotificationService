from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar("T")

class BaseNamespace(ABC, Generic[T]):

    @classmethod
    def get_namespace_name(cls):
        pass

    @abstractmethod
    async def ingest_data(self, data: T) -> None:
        pass

    @abstractmethod
    async def get_closest_matches(self, item: str) -> T:
        pass