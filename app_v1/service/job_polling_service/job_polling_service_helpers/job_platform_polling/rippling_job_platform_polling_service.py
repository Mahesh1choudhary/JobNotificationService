import asyncio
from typing import List

import httpx

from app_v1.commons.service_logger import setup_logger
from app_v1.commons.time_utils import current_time_in_utc
from app_v1.database.database_models.company_job_source_model import CompanyJobSourceModel, FetchConfig
from app_v1.models.request_models.job_creation_request import JobCreationRequest
from app_v1.service.job_polling_service.job_polling_service_helpers.job_platform_polling.base_job_platform_polling_service import \
    JobPlatformPollingService

logger = setup_logger()

class RipplingJobPlatformPollingService(JobPlatformPollingService):
    pass