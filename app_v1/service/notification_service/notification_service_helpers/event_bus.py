import asyncio
from collections import defaultdict
from typing import Dict, List

from app_v1.service.notification_service.notification_service_helpers.event_models import EventType, BaseEvent
from app_v1.service.notification_service.notification_service_helpers.event_handlers import BaseEventHandler

class EventBus():
    def __init__(self):
        self._registered_handlers: Dict[EventType, List[BaseEventHandler]] = defaultdict(list)

    def register_handler(self, event_type: EventType, handler:BaseEventHandler):
        self._registered_handlers[event_type].append(handler)


    async def dispatch_event(self, event: BaseEvent):
        handlers_for_given_event = self._registered_handlers.get(event.event_type, [])
        if not handlers_for_given_event:
            return
        #TODO: should it be fire and forget or wait for all to complete?
        await asyncio.gather(*(handler.handle_event(event) for handler in handlers_for_given_event), return_exceptions=True)

