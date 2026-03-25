from app_v1.service.notification_service.notification_service import NotificationService
from app_v1.service.notification_service.notification_service_helpers.event_models import BaseEvent, JobEvent


class BaseEventHandler():

    async def handle_event(self, event: BaseEvent):
        raise NotImplementedError()


class JobEventHandler(BaseEventHandler):

    def __init__(self, notification_service: NotificationService):
        self._notification_service= notification_service

    async def handle_event(self, event: JobEvent):
        self._notification_service.notify_for_job_event(event)