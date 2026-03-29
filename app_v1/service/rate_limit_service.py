from app_v1.config.config_classes_and_constants import DEFAULT_USER_NOTIFICATION_QUOTA
from app_v1.database.database_client import BaseDatabaseClient
from app_v1.database.repository.user_quota_repository import UserQuotaRepository


class RateLimitService:

    def __init__(self, database_client:BaseDatabaseClient):
        self._user_quota_repository = UserQuotaRepository(database_client)

    async def allow_notification(self, user_id:int) -> bool:
        await self._user_quota_repository.create_if_not_exists(user_id, DEFAULT_USER_NOTIFICATION_QUOTA) #TODO: should be created when new used is created, but for now adding here with default quota
        notification_allowed:bool =  await self._user_quota_repository.allow_if_possible(user_id)
        return notification_allowed

    async def reset_user_notification_quota(self, user_id:int, new_quota) -> None:
        await self._user_quota_repository.create_if_not_exists(user_id, new_quota) #TODO: should be created when new used is created, but for now adding here with 0 quota
        await self._user_quota_repository.reset_user_notification_quota(user_id, new_quota)

