import asyncio
import threading

from app_v1.database.database_client import DatabaseClientFactory
from app_v1.database.database_config import BaseDatabaseConfig


class DatabaseManager():

    def __init__(self, database_config: BaseDatabaseConfig):
        self.database_client = DatabaseClientFactory.create_database_client(database_config)

    async def init(self):
        await self.database_client.init()

    async def close(self):
        await self.database_client.close()

