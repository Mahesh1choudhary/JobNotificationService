import asyncio
import threading
from abc import ABC, abstractmethod
from typing import Optional

from app_v1.database.database_config import PostgresSQLDatabaseConfig, BaseDatabaseConfig


class BaseDatabaseClient(ABC):

    def __init__(self, config: BaseDatabaseConfig):
        self._database_config = BaseDatabaseConfig

    @abstractmethod
    async def init(self):
        pass

    @abstractmethod
    async def close(self):
        pass

    @abstractmethod
    def get_pool(self):
        pass



class PostgresSQLDatabaseClient(BaseDatabaseClient):

    _thread_lock = threading.Lock()
    _instance: Optional[PostgresSQLDatabaseClient] = None


    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._thread_lock:
                if cls._instance is not None:
                    return cls._instance
                cls._instance = super(PostgresSQLDatabaseClient, cls).__new__(cls, *args, **kwargs)

        return cls._instance

    def __init__(self, config: PostgresSQLDatabaseConfig):
        if getattr(self, '_constructed', False):
            if self._database_config != config:
                raise ValueError("PostgresSQL database client already initialized with different config. ")
            return

        super().__init__(config)
        self._constructed = True
        self._initialized = False
        self.async_lock = asyncio.Lock()


    async def init(self):
        if self._initialized:
            return

        async with self.async_lock:
            if self._initialized:
                return

            self._initialized = True
            #TODO: remaining initialization


    async def close(self):
        pass


    def get_pool(self):
        pass





class DatabaseClientFactory():

    _database_client_classes = {
        PostgresSQLDatabaseConfig.get_database_name(): PostgresSQLDatabaseClient,
    }


    @classmethod
    def create_database_client(cls, database_config: BaseDatabaseConfig) -> BaseDatabaseClient:
        backend_database_name =  database_config.get_database_name()
        if backend_database_name not in cls._database_client_classes:
            available_database_clients = ", ".join(cls._database_client_classes.keys())
            raise ValueError(f"No valid Database client exists for database_name: {backend_database_name}. Available database clients: {available_database_clients}")

        return cls._database_client_classes[backend_database_name](database_config)

