from app_v1.service.notification_service.notification_service_helpers.event_bus import EventBus
from app_v1.service.notification_service.notification_service_helpers.event_models import BaseEvent


class BaseEventPublisher():

    async def publish(self, event: BaseEvent):
        raise NotImplementedError



class InMemoryEventPublisher(BaseEventPublisher):

    def __init__(self, event_bus):
        self._event_bus:EventBus = event_bus

    async def publish(self, event: BaseEvent):
        await self._event_bus.dispatch_event(event)