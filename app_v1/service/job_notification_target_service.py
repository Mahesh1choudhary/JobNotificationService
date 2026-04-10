from app_v1.commons.service_logger import setup_logger
from app_v1.database.database_client import BaseDatabaseClient
from app_v1.database.database_models.job_notification_targets import JobNotificationTarget
from app_v1.database.database_models.user import User
from app_v1.database.repository.job_notification_target_repository import JobNotificationTargetRepository
from app_v1.database.repository.user_repository import UserRepository
from app_v1.models.data_models.job_tag_response import JobTagResponse

logger = setup_logger()
class JobNotificationTargetService():

    def __init__(self, database_client: BaseDatabaseClient):
        self._job_notification_target_repository = JobNotificationTargetRepository(database_client)
        self._user_repository = UserRepository(database_client)


    async def find_job_notification_target_users(self, job_tag_response: JobTagResponse) -> list[User]:
        job_notification_target:JobNotificationTarget = await self._job_notification_target_repository.get_job_notification_target_by_job_tags(job_tag_response)
        if job_notification_target is None:
            return []

        target_user_ids:list[int] = job_notification_target.user_ids
        target_users: list[User] = await self._user_repository.find_all_by_user_ids(target_user_ids)
        logger.info(f"[{self.__class__.__name__}]-[{self.find_job_notification_target_users.__name__}]: {len(target_users)} target users for job_tag_response: {job_tag_response}")

        return target_users

