import asyncio
import json
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

    _thread_local = threading.local() # each thread will have different instances


    def __new__(cls, *args, **kwargs):
        if not hasattr(cls._thread_local, "instance"):
            cls._thread_local.instance = super(PostgresSQLDatabaseClient, cls).__new__(cls)

        return cls._thread_local.instance

    def __init__(self, config: PostgresSQLDatabaseConfig):
        if getattr(self, '_initialized_instance', False):
            if self._database_config != config:
                raise ValueError("PostgresSQL database client already initialized with different config.")
            return

        super().__init__(config)
        self._initialized_instance = True
        self._initialized = False
        self.async_lock = asyncio.Lock()
        self._connection_pool = None

    @staticmethod
    async def setup_connection(conn):
        """This runs for every new connection in the pool, to avoid manual converting of jsons to dict or reverse"""
        await conn.set_type_codec(
            'jsonb',
            encoder=json.dumps,
            decoder=json.loads,
            schema='pg_catalog'
        )


    async def init(self):
        if self._initialized:
            return
        try:
            async with self.async_lock:
                if self._initialized:
                    return

                self._connection_pool = await asyncpg.create_pool(
                    user= self._database_config.postgresSQL_db_user,
                    password= self._database_config.postgresSQL_db_password,
                    database= self._database_config.postgresSQL_db_name,
                    host= self._database_config.postgresSQL_db_host,
                    port= self._database_config.postgresSQL_db_port,
                    ssl="require",
                    min_size= self._database_config.postgresSQL_db_connection_pool_min,
                    max_size= self._database_config.postgresSQL_db_connection_pool_max,
                    init= self.setup_connection
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

