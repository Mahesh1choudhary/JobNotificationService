from abc import ABC
from typing import List

from app_v1.commons.service_logger import setup_logger
from app_v1.database.database_client import BaseDatabaseClient

logger = setup_logger()
class BaseVectorRepository():

    def __init__(self, _database_client:BaseDatabaseClient, table_name:str):
        self._database_client = _database_client
        self._table_name = table_name


    async def insert_record(self, data: dict):
        columns = ", ".join(data.keys())
        placeholder_list = []

        processed_values = []
        for i, (key,value) in enumerate(data.items()):
            p = f"${i+1}"
            #TODO: currently embedding is hard coded, update in future
            if key == "embedding":
                p = f"{p}::vector"
                processed_values.append(str(value))
            else:
                processed_values.append(value)
            placeholder_list.append(p)

        placeholders = ", ".join(placeholder_list)

        query = f"""
            INSERT INTO {self._table_name} ({columns})
            VALUES ({placeholders})
            ON CONFLICT DO NOTHING
        """

        try:
            await self._database_client.execute(query, *processed_values)
        except Exception:
            logger.error(f"Database Error in insert_record", exc_info=True)
            raise




    async def vector_search(self, embedding: List[float], limit:int, columns_to_extract:List[str]):
        embedding_column_name = "embedding" #TODO: should be like this, one thing changed, everything will breakdown

        score_alias = f"(1 - ({embedding_column_name} <=> $1::vector)) AS similarity_score" # higher value means more similar or matching
        cols_string = ", ".join(columns_to_extract + [score_alias])
        query = f"""
            SELECT {cols_string} FROM {self._table_name} 
            ORDER BY {embedding_column_name} <=> $1::vector 
            LIMIT $2
        """
        #TODO: cosine search for now, if changed, update index in schema.sql and other places accordingly
        #TODO: update the embedding model, tables , etc accordingly with any change

        try:
            rows = await self._database_client.fetch(query, str(embedding), limit)
            return rows
        except Exception:
            logger.error(f"Database Error in vector_search", exc_info=True)
            raise

    async def full_text_search(self, item_text:str, limit:int , columns_to_extract:List[str] ):
        cols_string = ", ".join(columns_to_extract)
        query = f"""
            SELECT {cols_string}, ts_rank(fts_tokens, plainto_tsquery('english', $1)) as fts_rank
            FROM {self._table_name} 
            WHERE fts_tokens @@ plainto_tsquery('english', $1)
            ORDER BY fts_rank DESC
            LIMIT $2 
        """

        try:
            if not item_text.strip():
                return []
            rows = await self._database_client.fetch(query, item_text, limit)
            return rows
        except Exception:
            logger.error(f"Database Error in {self.full_text_search.__name__}", exc_info=True)
            raise


    async def get_all_data(self, columns_to_extract:List[str]):
        cols_string = ", ".join(columns_to_extract)
        query = f"""
            SELECT {cols_string}
            FROM {self._table_name}
        """
        try:
            rows = await self._database_client.fetch(query)
            return rows
        except Exception:
            logger.error(f"Database Error in {self.get_all_data.__name__}", exc_info=True)
            raise

    async def get_data_by_id(self, item_id:int, columns_to_extract:List[str]):
        cols_string = ", ".join(columns_to_extract)
        query = f"""
            SELECT {cols_string} 
            FROM {self._table_name}
            WHERE id=$1
        """
        try:
            row = await self._database_client.fetchrow(query, item_id)
            return row
        except Exception:
            logger.error(f"Database Error in {self.get_data_by_id.__name__}", exc_info=True)
            raise
