from app_v1.commons.service_logger import setup_logger
from app_v1.service.job_polling_service.job_polling_service_helpers.job_platform_polling.ashbyhq_job_platform_polling_service import \
    AshbyhqJobPlatformPollingService
from app_v1.service.job_polling_service.job_polling_service_helpers.job_platform_polling.base_job_platform_polling_service import \
    JobPlatformPollingService
from app_v1.service.job_polling_service.job_polling_service_helpers.job_platform_polling.greenhouse_job_platform_polling_service import \
    GreenhouseJobPlatformPollingService
from app_v1.service.job_polling_service.job_polling_service_helpers.job_platform_polling.mynexthire_job_platform_polling_service import \
    MynexthireJobPlatformPollingService
from app_v1.service.job_polling_service.job_polling_service_helpers.job_platform_polling.rippling_job_platform_polling_service import \
    RipplingJobPlatformPollingService
from app_v1.service.job_polling_service.job_polling_service_helpers.job_platform_polling.uber_job_platform_polling_service import \
    UberJobPlatformPollingService

logger = setup_logger()
class JobPlatformPollingServiceFactory:

    # names are as per in the database table job_platforms
    _platform_registry = {
        "greenhouse": GreenhouseJobPlatformPollingService,
        "mynexthire": MynexthireJobPlatformPollingService,
        "rippling": RipplingJobPlatformPollingService,
        "uber": UberJobPlatformPollingService,
        "ashbyhq": AshbyhqJobPlatformPollingService,
        "default": JobPlatformPollingService
    }

    @classmethod
    def get_job_platform_polling_service(cls, platform_name: str) -> JobPlatformPollingService | None:

        job_platform_polling_service = cls._platform_registry.get(platform_name, None)
        if job_platform_polling_service is None:
            logger.warning(f"[{cls.__class__.__name__}]-[{cls.get_job_platform_polling_service.__name__}]:No platform_polling_service found for {platform_name}")
            return None
        return job_platform_polling_service()