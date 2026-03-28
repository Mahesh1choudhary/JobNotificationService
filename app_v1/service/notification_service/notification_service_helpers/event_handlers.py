from app_v1.commons.service_logger import setup_logger
from app_v1.database.database_client import BaseDatabaseClient
from app_v1.database.database_models.user import User
from app_v1.service.job_notification_target_service import JobNotificationTargetService
from app_v1.service.notification_service.notification_service import NotificationService
from app_v1.service.notification_service.notification_service_helpers.event_models import BaseEvent, JobEvent

logger = setup_logger()

class BaseEventHandler():

    async def  handle_event(self, event: BaseEvent):
        raise NotImplementedError()


class JobEventHandler(BaseEventHandler):

    def __init__(self, database_client: BaseDatabaseClient):
        self._notification_service= NotificationService(database_client)
        self._job_notification_targets_service = JobNotificationTargetService(database_client)

    async def handle_event(self, event: JobEvent):
        try:
            target_users: list[User] = await self._job_notification_targets_service.find_job_notification_target_users(event.job_tag_response)

            await self._notification_service.send_notification_to_targets(target_users= target_users, notification_message= event.job_notification_message)
        except Exception as exc:
            logger.error("Error handling JobEvent", exc_info=True)
            raise