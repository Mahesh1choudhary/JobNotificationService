from typing import List, Dict
import asyncio
from app_v1.database.database_client import BaseDatabaseClient
from app_v1.database.repository.vector_repository import BaseVectorRepository
from app_v1.database.tables import DatabaseTables
from app_v1.llm.llm_manager import LLMManager
from app_v1.llm.llm_model.embedding_model import EmbeddingModel
from app_v1.vector_data.base_namespace import BaseNamespace
from app_v1.vector_data.vector_data_models.job_department_name_vector import JobDepartmentNameVector

llm_manager = LLMManager()
class JobDepartmentNameNamespace(BaseNamespace[JobDepartmentNameVector]):

    def __init__(self, database_client:BaseDatabaseClient):
        self._database_client = database_client
        self._table_name = DatabaseTables.JOB_DEPARTMENT_NAME_TABLE.value
        self._job_department_name_vector_repository = BaseVectorRepository(self._database_client, self._table_name)

    @classmethod
    def get_namespace_name(cls):
        return "job_department_name_namespace"

    #TODO: need to add batch ingesting
    async def ingest_embedding_data(self, data: JobDepartmentNameVector):
        #TODO: reconsider what to embed
        text_to_embed = f"{data.department_name}, {data.description}"
        embedding_model:EmbeddingModel = llm_manager.get_embedding_model()
        embeddings = await embedding_model.get_embeddings(text_to_embed)

        data_to_insert = data.model_dump()
        #TODO: column name "embedding" is hard coded at most places, recheck
        data_to_insert["embedding"] = embeddings
        await self._job_department_name_vector_repository.insert_record(data_to_insert)


    async def ingest_embedding_data_batch(self, data_list: List[JobDepartmentNameVector]):
        if not data_list:
            return
        embedding_model: EmbeddingModel = llm_manager.get_embedding_model()
        # Prepare texts for embedding
        texts_to_embed = [f"{d.department_name}, {d.description}" for d in data_list]
        # Get embeddings concurrently
        embeddings = await asyncio.gather(*[embedding_model.get_embeddings(text) for text in texts_to_embed])
        # Prepare data dicts with embeddings
        data_dicts = []
        for d, emb in zip(data_list, embeddings):
            data_to_insert = d.model_dump()
            data_to_insert["embedding"] = emb
            data_dicts.append(data_to_insert)
        # Insert in batches of 100
        for i in range(0, len(data_dicts), 100):
            batch = data_dicts[i:min(i+100,len(data_dicts))]
            await self._job_department_name_vector_repository.insert_records(batch)


    async def get_closest_matches(self, item: str, similarity_threshold: float,limit:int = 5, ranking_constant:int = 60) -> List[JobDepartmentNameVector]:
        embedding_model:EmbeddingModel = llm_manager.get_embedding_model()
        embeddings = await embedding_model.get_embeddings(item)

        column_to_extract = list(JobDepartmentNameVector.model_fields.keys())

        # limit+20, so that there are enough data for ranking
        vector_search_closest_matches = await self._job_department_name_vector_repository.vector_search(embeddings, limit+20, column_to_extract)

        full_text_search_closest_matches = await self._job_department_name_vector_repository.full_text_search(item, limit+20, column_to_extract)

        final_scores:Dict[str, float] = {} # {department_name: score}
        data_objects: Dict[str, JobDepartmentNameVector] = {}
        for rank, match in enumerate(vector_search_closest_matches, start=1):
            data: JobDepartmentNameVector = JobDepartmentNameVector(**match)
            data_objects[data.department_name] = data
            final_scores[data.department_name] = final_scores.get(data.department_name, 0) + (1/(ranking_constant + rank))

        for rank, match in enumerate(full_text_search_closest_matches, start=1):
            data: JobDepartmentNameVector= JobDepartmentNameVector(**match)
            data_objects[data.department_name] = data
            final_scores[data.department_name] = final_scores.get(data.department_name, 0) + (1/(ranking_constant + rank))

        sorted_scores = sorted(final_scores.items(), key=lambda item: item[1], reverse=True)

        final_results: List[JobDepartmentNameVector] = []
        for item, score in sorted_scores[:limit]:
            final_results.append(data_objects[item])

        return final_results

