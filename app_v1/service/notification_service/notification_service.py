import asyncio
from typing import List

from app_v1.commons.service_logger import setup_logger
from app_v1.database.database_client import BaseDatabaseClient
from app_v1.database.database_models.user import User
from app_v1.database.repository.job_notification_target_repository import JobNotificationTargetRepository
from app_v1.service.notification_service.notification_service_helpers.notification_sender import NotificationSender, \
     TelegramNotificationSender
from app_v1.service.rate_limit_service import RateLimitService

logger = setup_logger()

class NotificationService():
    def __init__(self, database_client:BaseDatabaseClient):
        self._job_notification_target_repository= JobNotificationTargetRepository(database_client)
        self._notification_senders:List[NotificationSender] = [TelegramNotificationSender()]#TODO: For now using telegram to avoid cost and rate limiting
        self._notification_rate_limiter = RateLimitService(database_client)


    async def send_notification_to_targets(self, target_users: List[User], notification_message:str):
        #TODO: notification sender should be user specific when sending

        tasks = []
        for user in target_users:
            if self._notification_rate_limiter.allow_notification(user_id=user.user_id):
                #TODO: for now single check for all senders, need to change in future ans different senders has different cost. ALso one sender ot two sender have same check is not a equality
                for sender in self._notification_senders:
                    tasks.append(sender.send_notification(user, notification_message))
            else:
                logger.info(f"Sending Notification not allowed for user: {user.user_name}")

        results = await asyncio.gather(*tasks, return_exceptions=True)

        #TODO: For failing ones- should we retry or just log
        for res in results:
            if isinstance(res, Exception):
                logger.error(f"Notification failed: {res}")
