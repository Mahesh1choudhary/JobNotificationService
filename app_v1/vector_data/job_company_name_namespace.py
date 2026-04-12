from typing import Any, List, Dict
from app_v1.database.database_client import BaseDatabaseClient
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
        text_to_embed = f"{data.company_name}, {data.alias}"
        embedding_model:EmbeddingModel = llm_manager.get_embedding_model()
        embeddings = await embedding_model.get_embeddings(text_to_embed)

        data_to_insert = data.model_dump()
        #TODO: column name "embedding" is hard coded at most places, recheck
        data_to_insert["embedding"] = embeddings
        await self._job_company_name_vector_repository.insert_record(data_to_insert)


    async def get_closest_matches(self, item: str, similarity_threshold: float,limit:int = 5, ranking_constant:int = 60) -> List[JobCompanyNameVector]:
        embedding_model:EmbeddingModel = llm_manager.get_embedding_model()
        embeddings = await embedding_model.get_embeddings(item)

        column_to_extract = ["company_name", "alias"]

        # limit+20, so that there are enough data for ranking
        vector_search_closest_matches = await self._job_company_name_vector_repository.vector_search(embeddings, limit+20, column_to_extract)

        full_text_search_closest_matches = await self._job_company_name_vector_repository.full_text_search(item, limit+20, column_to_extract)

        final_scores:Dict[str, float] = {} # {company_name: score}
        data_objects: Dict[str, JobCompanyNameVector] = {}
        for rank, match in enumerate(vector_search_closest_matches, start=1):
            if match["similarity_score"] < similarity_threshold:
                break
            data: JobCompanyNameVector = JobCompanyNameVector(**match)
            data_objects[data.company_name] = data
            final_scores[data.company_name] = final_scores.get(data.company_name, 0) + (1/(ranking_constant + rank))

        for rank, match in enumerate(full_text_search_closest_matches, start=1):
            data: JobCompanyNameVector = JobCompanyNameVector(**match)
            data_objects[data.company_name] = data
            final_scores[data.company_name] = final_scores.get(data.company_name, 0) + (1/(ranking_constant + rank))

        sorted_scores = sorted(final_scores.items(), key=lambda item: item[1], reverse=True)

        final_results: List[JobCompanyNameVector] = []
        for item, score in sorted_scores[:limit]:
            final_results.append(data_objects[item])

        return final_results



