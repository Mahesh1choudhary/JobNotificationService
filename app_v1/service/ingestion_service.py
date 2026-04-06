from typing import Dict, Any

from app_v1.database.database_client import BaseDatabaseClient
from app_v1.models.request_models.ingestion_request import NamespaceType, IngestionRequest
from app_v1.vector_data.job_company_name_namespace import JobCompanyNameNamespace
from app_v1.vector_data.job_location_namespace import JobLocationNamespace


class IngestionService():

    def __init__(self, database_client:BaseDatabaseClient):
        self._namespace_mapping: Dict[str, Any] = {
            NamespaceType.JOB_COMPANY_NAME_NAMESPACE: JobCompanyNameNamespace(database_client=database_client),
            NamespaceType.JOB_LOCATION_NAMESPACE: JobLocationNamespace(database_client=database_client),
        }


    async def ingest_data(self, ingestion_request: IngestionRequest):
        namespace_instance = self._namespace_mapping[ingestion_request.namespace_type]
        if not namespace_instance:
            raise ValueError(f"Namespace {ingestion_request.namespace_type} not supported; available ones : {",".join(self._namespace_mapping.keys())}")

        #TODO: need to add batch ingesting in the namespace
        #TODO: need to convert into lower cases
        ingestion_data = ingestion_request.data
        for single_ingestion in ingestion_data:
            await namespace_instance.ingest_data(single_ingestion)