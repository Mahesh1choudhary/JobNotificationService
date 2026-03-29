import asyncpg

from app_v1.commons.service_logger import setup_logger
from app_v1.database.database_client import BaseDatabaseClient
from app_v1.database.tables import DatabaseTables

logger = setup_logger()

class UserQuotaRepository:

    def __init__(self, database_client:BaseDatabaseClient):
        self._database_client:BaseDatabaseClient = database_client


    async def allow_if_possible(self, user_id:int) -> bool:
        query = f"""
                UPDATE {DatabaseTables.USER_QUOTA_TABLE.value}
                SET used_count = used_count + 1
                WHERE user_id = $1
                  AND used_count < total_count
                RETURNING 1
                """
        try:
            row = await self._database_client.fetchrow(query, user_id)
            return row is not None
        except Exception as exc:
            logger.error("Error in allow_if_possible", exc_info=True)
            raise


    async def reset_user_notification_quota(self, user_id:int, new_quota:int):
        query = f"""
                UPDATE {DatabaseTables.USER_QUOTA_TABLE.value}
                SET total_count = $2,
                    used_count = 0
                WHERE user_id = $1
                """
        try:
            row = await self._database_client.fetchrow(query, user_id, new_quota)
            return row is not None
        except Exception as exc:
            logger.error("Error in allow_if_possible", exc_info=True)
            raise

    async def create_if_not_exists(self, user_id:int, user_quota:int):
        query = f"""
            INSERT INTO {DatabaseTables.USER_QUOTA_TABLE.value} (user_id, total_count, used_count)
            VALUES ($1, $2, 0)
            ON CONFLICT (user_id) DO NOTHING;
            """

        try:
            row = await self._database_client.fetchrow(query, user_id, user_quota)
        except Exception as exc:
            logger.error("Error in create_if_not_exists", exc_info=True)
            raise