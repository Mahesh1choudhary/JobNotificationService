import threading

from app_v1.llm.llm_model.base_llm_model import LLMModel
from app_v1.llm.llm_model.embedding_model import EmbeddingModel


class LLMManager():
    _thread_local = threading.local() # each thread will have different instances

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls._thread_local, "instance"):
           cls._thread_local.instance = super(LLMManager, cls).__new__(cls)

        return cls._thread_local.instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.tag_generation_model:LLMModel = None
            self.embedding_model:EmbeddingModel = None


    def set_tag_generation_model(self, model:LLMModel):
        self.tag_generation_model = model


    def get_tag_generation_model(self) -> LLMModel:
        if self.tag_generation_model is None:
            raise ValueError("tag_generation_model is not set")
        return self.tag_generation_model

    def set_embedding_model(self, model: EmbeddingModel):
        self.embedding_model:EmbeddingModel = model

    def get_embedding_model(self) -> EmbeddingModel:
        if self.embedding_model is None:
            raise ValueError("embedding_model is not set")
        return self.embedding_model


