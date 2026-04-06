from app_v1.commons.service_logger import setup_logger
from app_v1.database.database_client import BaseDatabaseClient
from app_v1.database.repository.job_notification_target_repository import JobNotificationTargetRepository
from app_v1.models.data_models.user_interest import UserInterest
from app_v1.models.request_models.user_preference_request import UserPreferenceRequest

logger = setup_logger()

class UserPreferencesService():

    def __init__(self, database_client:BaseDatabaseClient):
        self._database_client = database_client
        self._user_preference_repository = JobNotificationTargetRepository(self._database_client)

    async def add_user_preferences(self, user_id:int, user_preferences: UserPreferenceRequest):
        try:
            result = await self._user_preference_repository.add_user_preferences(user_id, user_preferences)
            return result
        except Exception as exc:
            logger.error("Error in add_user_preferences in UserPreferencesService", exc_info=True)
            raise


    async def remove_user_preferences(self, user_id:int , user_preferences: UserPreferenceRequest):
        try:
            result = await self._user_preference_repository.remove_user_preferences(user_id, user_preferences)
            return result
        except Exception as exc:
            logger.error("Error in add_user_preferences in UserPreferencesService", exc_info=True)
            raise

    async def add_new_user_interest_row(self, user_interest_row: UserInterest):
        try:
            result = await self._user_preference_repository.remove_user_preferences(user_id, user_preferences)
            return result
        except Exception as exc:
            logger.error("Error in  add_new_user_interest_row in UserPreferencesService", exc_info=True)
            raise
