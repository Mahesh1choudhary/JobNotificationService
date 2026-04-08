import httpx

from app_v1.commons.service_logger import setup_logger
from app_v1.database.database_models.company_job_source_model import CompanyJobSourceModel
from app_v1.service.job_polling_service.job_polling_service_helpers.job_platform_polling.base_job_platform_polling_service import JobPlatformPollingService

logger = setup_logger()
class GreenhouseJobPlatformPollingService(JobPlatformPollingService):

    async def fetch_and_ingest_job_data_for_company(self, job_company_job_source:CompanyJobSourceModel):
        try:
            fetch_job_list_url = job_company_job_source.fetch_job_list_url
            if fetch_job_list_url is None:
                logger.warning(f"fetch_job_url not set for company_id: {job_company_job_source.company_id}")

            #fethcing company jobs data
            #TODO: need to add retries
            async with httpx.AsyncClient() as client:
                response = await client.get(fetch_job_list_url)

            company_jobs_data = response.json()["jobs"]

            for job_data in company_jobs_data:
                await self.process_job_data(job_data)
            pass
        #TODO: need to add logic here

        except Exception as exc:
            logger.error(f"Error in {self.fetch_and_ingest_job_data_for_company.__name__}", exc_info=exc)




    async def process_job_data(self, job_data: dict):
        pass







