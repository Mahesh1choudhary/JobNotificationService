from typing import List

from openai import AsyncOpenAI

from app_v1.commons.service_logger import setup_logger
from app_v1.config.config_keys import OPENAI_API_KEY
from app_v1.config.config_loader import fetch_key_value

logger = setup_logger()
class EmbeddingModel():

    def __init__(self):
        self.embedding_model_name: str = "text-embedding-3-small"
        try:
            open_api_key = fetch_key_value(OPENAI_API_KEY, str)
            if not open_api_key:
                raise ValueError("API key is not provided")
            self.client = AsyncOpenAI(api_key=open_api_key)
        except Exception as e:
            logger.error(f"Error initializing {self.get_model_name()}", exc_info=True)
            raise

    def get_model_name(self) -> str:
        return self.embedding_model_name
        #TODO: change the table, schemas, etc accordingly when model is changed

    async def get_embeddings(self, text: str) -> List[float]:
        try:
            response = await self.client.embeddings.create(
                input=[text],
                model = self.embedding_model_name
            )
            return response.data[0].embedding
        except Exception as exc:
            logger.error(f"Error getting embeddings from {self.get_model_name()}", exc_info=True)
            raise