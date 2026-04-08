from typing import Any, List

from app_v1.database import database_client
from app_v1.database.database_client import BaseDatabaseClient
from app_v1.database.database_config import DatabaseConfigFactory
from app_v1.database.database_manager import DatabaseManager
from app_v1.database.repository.vector_repository import BaseVectorRepository
from app_v1.database.tables import DatabaseTables
from app_v1.llm.llm_manager import LLMManager
from app_v1.llm.llm_model.embedding_model import EmbeddingModel
from app_v1.vector_data.base_namespace import BaseNamespace
from app_v1.vector_data.vector_data_models.job_company_name_vector import JobCompanyNameVector

llm_manager = LLMManager()
class JobCompanyNameNamespace(BaseNamespace[JobCompanyNameVector]):

    def __init__(self, database_client:BaseDatabaseClient):
        self._database_client = database_client
        self._table_name = DatabaseTables.JOB_COMPANY_NAME_TABLE.value
        self._job_company_name_vector_repository = BaseVectorRepository(self._database_client, self._table_name)

    @classmethod
    def get_namespace_name(cls):
        return "job_company_namespace"

    #TODO: need to add batch ingesting
    async def ingest_embedding_data(self, data: JobCompanyNameVector):
        #TODO: reconsider what to embed
        text_to_embed = f"{data.company_name}, {data.description}"
        embedding_model:EmbeddingModel = llm_manager.get_embedding_model()
        embeddings = await embedding_model.get_embeddings(text_to_embed)

        data_to_insert = data.model_dump()
        #TODO: column name "embedding" is hard coded at most places, recheck
        data_to_insert["embedding"] = embeddings
        await self._job_company_name_vector_repository.insert_record(data_to_insert)


    async def get_closest_matches(self, item: str, limit:int = 5) -> List[JobCompanyNameVector]:
        embedding_model:EmbeddingModel = llm_manager.get_embedding_model()
        embeddings = await embedding_model.get_embeddings(item)

        column_to_extract = list(JobCompanyNameVector.model_fields.keys())
        closest_matches = await self._job_company_name_vector_repository.vector_search(embeddings, limit, column_to_extract)

        return [JobCompanyNameVector(**match) for match in closest_matches]



