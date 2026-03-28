from enum import Enum
from typing import Literal

from pydantic import BaseModel

from app_v1.models.data_models.job_tag_response import JobTagResponse


class EventType(str, Enum):
    JOB_EVENT = "JOB_EVENT"


class BaseEvent(BaseModel):
    event_type: EventType

#TODO: update parameters as per the requirement
class JobEvent(BaseEvent):
    event_type: Literal[EventType.JOB_EVENT] = EventType.JOB_EVENT
    job_tag_response: JobTagResponse
    job_notification_message: str

