from app_v1.commons.service_logger import setup_logger
from app_v1.database.database_client import BaseDatabaseClient
from app_v1.database.database_models.user_preference import UserPreference
from app_v1.database.tables import DatabaseTables
from app_v1.models.request_models.user_preference_add_request import UserPreferenceRequest

logger = setup_logger()

class UserPreferenceRepository:

    def __init__(self, database_client:BaseDatabaseClient):
        self._database_client:BaseDatabaseClient = database_client


    async def add_user_preferences(self, user_id:int, input_user_preference: UserPreferenceRequest) -> None:
        query = f"""
            update {DatabaseTables.USER_PREFERENCE_TABLE.value} set
        """

        try:
            pass

        except Exception as exc:
            logger.error("Database error in add_user_preference", exc_info=True)
            raise

    async def remove_user_preferences(self, user_id:int, input_user_preferences: UserPreferenceRequest) -> None:
        query = f"""
            update {DatabaseTables.USER_PREFERENCE_TABLE.value} set
        """

        try:
            pass

        except Exception as exc:
            logger.error("Database error in add_user_preference", exc_info=True)
            raise
