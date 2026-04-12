from typing import List, Dict

from app_v1.database.database_client import BaseDatabaseClient
from app_v1.database.database_config import DatabaseConfigFactory
from app_v1.database.database_manager import DatabaseManager
from app_v1.database.repository.vector_repository import BaseVectorRepository
from app_v1.database.tables import DatabaseTables
from app_v1.llm.llm_manager import LLMManager
from app_v1.llm.llm_model.embedding_model import EmbeddingModel
from app_v1.llm.llm_model.gpt4o_mini_llm_model import GPT4OMiniLLMModel
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

    async def ingest_embedding_data(self, data: JobLocationVector):
        #TODO: reconsider what to embed
        text_to_embed = f"{data.job_location}, {data.alias}"
        embedding_model:EmbeddingModel = llm_manager.get_embedding_model()
        embeddings = await embedding_model.get_embeddings(text_to_embed)

        data_to_insert = data.model_dump()
        #TODO: column name "embedding" is hard coded at most places, recheck
        data_to_insert["embedding"] = embeddings
        await self._job_location_vector_repository.insert_record(data_to_insert)

    async def get_closest_matches(self, item: str, similarity_threshold: float,limit:int = 5, ranking_constant:int = 60) -> List[JobLocationVector]:
        #TODO: this can give wrong results as it tries to find best match, so completely different words can be best match if no other match is present
        embedding_model:EmbeddingModel = llm_manager.get_embedding_model()
        embeddings = await embedding_model.get_embeddings(item)

        column_to_extract = ["job_location", "alias"]

        # limit+20, so that there are enough data for ranking
        vector_search_closest_matches = await self._job_location_vector_repository.vector_search(embeddings, limit+20, column_to_extract)

        full_text_search_closest_matches = await self._job_location_vector_repository.full_text_search(item, limit+20, column_to_extract)

        #TODO: currently doing based on threshold, in future, will integrate in agent as tool call only
        final_scores:Dict[str, float] = {} # {job_location: score}
        data_objects: Dict[str, JobLocationVector] = {}
        for rank, match in enumerate(vector_search_closest_matches, start=1):
            if match["similarity_score"] < similarity_threshold:
                break
            data: JobLocationVector = JobLocationVector(**match)
            data_objects[data.job_location] = data
            final_scores[data.job_location] = final_scores.get(data.job_location, 0) + (1/(ranking_constant + rank))

        for rank, match in enumerate(full_text_search_closest_matches, start=1):
            data: JobLocationVector = JobLocationVector(**match)
            data_objects[data.job_location] = data
            final_scores[data.job_location] = final_scores.get(data.job_location, 0) + (1/(ranking_constant + rank))

        sorted_scores = sorted(final_scores.items(), key=lambda item: item[1], reverse=True)

        final_results: List[JobLocationVector] = []
        for item, score in sorted_scores[:limit]:
            final_results.append(data_objects[item])

        return final_results


    async def get_all_locations(self) -> List[JobLocationVector]:
        column_to_extract = ["job_location", "alias"]
        data = await self._job_location_vector_repository.get_all_data(column_to_extract)
        result:List[JobLocationVector] = []
        for item in data:
            result.append(JobLocationVector(**item))
        return result
