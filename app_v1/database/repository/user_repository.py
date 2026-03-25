from typing import Optional

from app_v1.commons.service_logger import setup_logger
from app_v1.database.database_models.user import User
from app_v1.database.database_client import BaseDatabaseClient
from app_v1.database.tables import DatabaseTables
from app_v1.models.request_models.user_creation_request import UserCreationRequest

logger = setup_logger()

class UserRepository():
    def __init__(self, database_client:BaseDatabaseClient):
        self._database_client:BaseDatabaseClient = database_client

    async def find_by_user_name(self, input_user_name:str) -> Optional[User]:
        user:Optional[User] =None
        query = f"""
        SELECT * from {DatabaseTables.USER_TABLE.value} WHERE user_name = $1 
        """

        try:
            row = await self._database_client.fetchrow(query, input_user_name)
            if row:
                return User(**dict(row))
            return None
        except Exception:
            logger.error(f"Database Error in find_by_user_name with user_name: {input_user_name}", exc_info=True)
            raise


    async def save_user(self, user_creation_request:UserCreationRequest):
        query = f"""
            INSERT INTO {DatabaseTables.USER_TABLE.value} (user_name, user_email)
            VALUES ($1, $2)
            ON CONFLICT (user_name) DO UPDATE 
            SET user_email = EXCLUDED.user_email,
                updated_at = NOW()
            RETURNING user_id, user_name, user_email, created_at, updated_at
        """
        try:
            row = await self._database_client.fetchrow(query, user_creation_request.user_name, user_creation_request.user_email)
            if not row:
                logger.warning(f"Database error in save_user: No row returned for user: {user_creation_request.user_name}")
                raise ValueError("User could not be saved or updated.")
            return User(**dict(row))
        except Exception:
            logger.error(f"Database Error in save_user with user_name: {user_creation_request.user_name}", exc_info=True)
            raise
