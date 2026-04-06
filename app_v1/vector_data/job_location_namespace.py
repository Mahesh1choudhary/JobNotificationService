from typing import List

from app_v1.database.database_client import BaseDatabaseClient
from app_v1.database.repository.vector_repository import BaseVectorRepository
from app_v1.database.tables import DatabaseTables
from app_v1.llm.llm_manager import LLMManager
from app_v1.llm.llm_model.embedding_model import EmbeddingModel
from app_v1.vector_data.base_namespace import BaseNamespace
from app_v1.vector_data.vector_data_models.job_location_vector import JobLocationVector

llm_manager = LLMManager()
class JobLocationNamespace(BaseNamespace[JobLocationVector]):

    def __init__(self, database_client: BaseDatabaseClient):
        self._database_client:BaseDatabaseClient = database_client
        self._table_name:str = DatabaseTables.JOB_LOCATION_TABLE.value
        self._job_location_vector_repository = BaseVectorRepository(database_client, self._table_name)

    @classmethod
    def get_namespace_name(cls):
        return "job_location_namespace"

    async def ingest_data(self, data: JobLocationVector):
        #TODO: reconsider what to embed
        text_to_embed = f"{data.job_location}, {data.description}"
        embedding_model:EmbeddingModel = llm_manager.get_embedding_model()
        embeddings = await embedding_model.get_embeddings(text_to_embed)

        data_to_insert = data.model_dump()
        #TODO: column name "embedding" is hard coded at most places, recheck
        data_to_insert["embedding"] = embeddings
        await self._job_location_vector_repository.insert_record(data_to_insert)

    async def get_closest_matches(self, item: str, limit:int = 5) -> List[JobLocationVector]:
        embedding_model:EmbeddingModel = llm_manager.get_embedding_model()
        embeddings = await embedding_model.get_embeddings(item)

        columns_to_extract = list(JobLocationVector.model_fields.keys())
        closest_matches = await self._job_location_vector_repository.vector_search(embeddings, limit, columns_to_extract)

        return [JobLocationVector(**match) for match in closest_matches]