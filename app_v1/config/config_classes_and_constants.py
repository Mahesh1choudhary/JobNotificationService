from typing import Any, Dict
from enum import Enum
from pydantic import BaseModel


class DatabaseWrapperConfig(BaseModel):
    database_name: str
    database_config_data: Dict[str, Any]



class EnvironmentConfigClass(Enum):
    ENV = "ENV"


TELEGRAM_BOT_NAME = "JobNotificationSenderBot"

DEFAULT_USER_NOTIFICATION_QUOTA = 100 # free number of notifications can be send to user