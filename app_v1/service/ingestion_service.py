import asyncio
from typing import Dict, Any, List

from app_v1.commons.service_logger import setup_logger
from app_v1.database.database_client import BaseDatabaseClient
from app_v1.database.database_models.company_job_source_model import CompanyJobSourceModel
from app_v1.database.repository.companies_job_sources_repository import CompaniesJobSourcesRepository
from app_v1.models.request_models.ingestion_request import NamespaceType, IngestionRequest, \
    CompanyJobSourceIngestionRequest
from app_v1.vector_data.job_company_name_namespace import JobCompanyNameNamespace
from app_v1.vector_data.job_department_name_namespace import JobDepartmentNameNamespace
from app_v1.vector_data.job_location_namespace import JobLocationNamespace

logger = setup_logger()
class IngestionService():

    def __init__(self, database_client:BaseDatabaseClient):
        self._namespace_mapping: Dict[str, Any] = {
            NamespaceType.JOB_COMPANY_NAME_NAMESPACE: JobCompanyNameNamespace(database_client=database_client),
            NamespaceType.JOB_LOCATION_NAMESPACE: JobLocationNamespace(database_client=database_client),
            NamespaceType.JOB_DEPARTMENT_NAME_NAMESPACE: JobDepartmentNameNamespace(database_client=database_client),
        }
        self._companies_job_sources_repository = CompaniesJobSourcesRepository(database_client=database_client)


    async def ingest_embedding_data(self, ingestion_request: IngestionRequest):
        namespace_instance = self._namespace_mapping[ingestion_request.namespace_type]
        if not namespace_instance:
            raise ValueError(f"Namespace {ingestion_request.namespace_type} not supported; available ones : {",".join(self._namespace_mapping.keys())}")

        #TODO: need to add batch ingesting in the namespace
        #TODO: need to convert into lower cases
        ingestion_data = ingestion_request.data
        for single_ingestion in ingestion_data:
            print(single_ingestion)
            await namespace_instance.ingest_embedding_data(single_ingestion)

    async def ingest_embedding_data_batch(self, ingestion_request: IngestionRequest):
        namespace_instance = self._namespace_mapping[ingestion_request.namespace_type]
        if not namespace_instance:
            raise ValueError(f"Namespace {ingestion_request.namespace_type} not supported; available ones : {",".join(self._namespace_mapping.keys())}")
        ingestion_data = ingestion_request.data
        await namespace_instance.ingest_embedding_data_batch(ingestion_data)

    #TODO: Create a batch based ingestion
    async def ingest_new_companies_job_sources(self, ingestion_request: List[CompanyJobSourceIngestionRequest]):
        try:
            tasks = [self._companies_job_sources_repository.insert_new_company_job_source(CompanyJobSourceModel(**company_job_source_request.model_dump()))
                     for company_job_source_request in ingestion_request]

            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as exc:
            logger.error(f"Error in {self.ingest_new_companies_job_sources.__name__}", exc_info=True)
            raise



