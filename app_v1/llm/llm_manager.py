import threading

from app_v1.llm.llm_model.base_llm_model import LLMModel
from app_v1.llm.llm_model.embedding_model import EmbeddingModel


class LLMManager():
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(LLMManager, cls).__new__(cls, *args, **kwargs)

        return cls._instance


    def set_tag_generation_model(self, model:LLMModel):
        self.tag_generation_model = model


    def get_tag_generation_model(self) -> LLMModel:
        if self.tag_generation_model is None:
            raise AttributeError("tag generation model is not set")
        return self.tag_generation_model

    def set_embedding_model(self, model: EmbeddingModel):
        self.embedding_model:EmbeddingModel = model

    def get_embedding_model(self) -> EmbeddingModel:
        if self.embedding_model is None:
            raise AttributeError("embedding model is not set")
        return self.embedding_model


