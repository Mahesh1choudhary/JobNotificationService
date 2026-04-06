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




    async def vector_search(self, embedding: List[float], limit, columns_to_extract:List[str]):
        embedding_column_name = "embedding" #TODO: should be like this, one thing changed, everything will breakdown
        cols_string = ", ".join(columns_to_extract)
        query = f"""
            SELECT {cols_string} FROM {self._table_name} ORDER BY {embedding_column_name} <=> $1::vector LIMIT $2
        """
        #TODO: cosine search for now, if changed, update index in schema.sql and other places accordingly
        #TODO: update the embedding model, tables , etc accordingly with any change

        try:
            rows = await self._database_client.fetch(query, str(embedding), limit)
            return rows
        except Exception:
            logger.error(f"Database Error in vector_search", exc_info=True)
            raise


