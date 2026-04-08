from typing import Any, Dict
from enum import Enum
from pydantic import BaseModel


class DatabaseWrapperConfig(BaseModel):
    database_name: str
    database_config_data: Dict[str, Any]


class GreenhousePollingConfig(BaseModel):
    jobs_api_url_template: str
    compressed_clients_relative_path: str
    whitelist_relative_path: str
    http_timeout_default: int = 10
    max_retries_default: int = 3
    poll_interval_seconds_default: float = 30.0


class EnvironmentConfigClass(Enum):
    ENV = "ENV"


TELEGRAM_BOT_NAME = "JobNotificationSenderBot"

DEFAULT_USER_NOTIFICATION_QUOTA = 100 # free number of notifications can be send to user