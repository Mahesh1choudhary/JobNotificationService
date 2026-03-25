from enum import Enum
from typing import Literal

from pydantic import BaseModel


class EventType(str, Enum):
    JOB_EVENT = "JOB_EVENT"


class BaseEvent(BaseModel):
    event_type: EventType

#TODO: update parameters as per the requirement
class JobEvent(BaseEvent):
    event_type: Literal[EventType.JOB_EVENT] = EventType.JOB_EVENT
    job_tags: list[str]
    job_info: str

