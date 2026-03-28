import asyncio
import threading
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Optional
import asyncpg

from app_v1.commons.service_logger import setup_logger
from app_v1.database.database_config import PostgresSQLDatabaseConfig, BaseDatabaseConfig

logger = setup_logger()

class BaseDatabaseClient(ABC):

    def __init__(self, config: BaseDatabaseConfig):
        self._database_config = config

    @abstractmethod
    async def init(self):
        pass

    @abstractmethod
    async def close(self):
        pass

    @abstractmethod
    def get_connection(self):
        pass



class PostgresSQLDatabaseClient(BaseDatabaseClient):

    _thread_lock = threading.Lock()
    _instance: Optional[PostgresSQLDatabaseClient] = None


    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._thread_lock:
                if cls._instance is not None:
                    return cls._instance
                cls._instance = super(PostgresSQLDatabaseClient, cls).__new__(cls)

        return cls._instance

    def __init__(self, config: PostgresSQLDatabaseConfig):
        if getattr(self, '_constructed', False):
            if self._database_config != config:
                raise ValueError("PostgresSQL database client already initialized with different config. ")
            return

        self._database_config: PostgresSQLDatabaseConfig = None
        super().__init__(config)
        self._constructed = True
        self._initialized = False
        self.async_lock = asyncio.Lock()


    async def init(self):
        if self._initialized:
            return
        try:
            async with self.async_lock:
                if self._initialized:
                    return

                #database_url = f"postgresql+asyncpg://{self._database_config.postgresSQL_db_name}:{self._database_config.postgresSQL_db_password}@{self._database_config.postgresSQL_db_host}:{self._database_config.postgresSQL_db_port}/{self._database_config.postgresSQL_db_name}?sslmode=require"

                self._connection_pool = await asyncpg.create_pool(
                    user= self._database_config.postgresSQL_db_user,
                    password= self._database_config.postgresSQL_db_password,
                    database= self._database_config.postgresSQL_db_name,
                    host= self._database_config.postgresSQL_db_host,
                    port= self._database_config.postgresSQL_db_port,
                    ssl="require",
                    min_size= self._database_config.postgresSQL_db_connection_pool_min,
                    max_size= self._database_config.postgresSQL_db_connection_pool_max,
                )
                self._initialized = True
            logger.info("PostgresSQL database client initialized")
        except Exception as e:
            logger.error("Error initializing postgresSQL database client", exc_info=True)
            raise


    async def close(self):
        if self._connection_pool:
            await self._connection_pool.close()
            self._connection_pool = None
            self._initialized = False

    @asynccontextmanager
    async def get_connection(self):
        if not self._initialized or not self._connection_pool:
            raise RuntimeError("Database client not initialized")

        async with self._connection_pool.acquire() as conn:
            yield conn


    @asynccontextmanager
    async def transaction(self):
        async with self.get_connection() as conn:
            async with conn.transaction():
                yield conn


    async def fetch(self, query:str, *args):
        # returns all rows
        async with self.get_connection() as conn:
            return await conn.fetch(query, *args)


    async def fetchrow(self, query:str, *args):
        # returns first row
        async with self.get_connection() as conn:
            return await conn.fetchrow(query, *args)

    async def execute(self, query:str, *args):
        async with self.transaction() as conn:
            return await conn.execute(query, *args)

    async def executemany(self, query: str, args_list):
        async with self.transaction() as conn:
            await conn.executemany(query, args_list)


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

