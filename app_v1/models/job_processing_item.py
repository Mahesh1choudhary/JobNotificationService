from typing import Any

from pydantic import BaseModel, ConfigDict

from app_v1.service.job_polling_service.job_polling_service_helpers.job_platform_polling.base_job_platform_polling_service import \
    JobPlatformPollingService


class JobProcessingItem(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True) # to allow custom classes

    job_platform_polling_service: JobPlatformPollingService
    job_data_item: dict[Any, Any]
    job_company_id: int