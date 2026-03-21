from abc import ABC, abstractmethod

class LLMModel(ABC):

    @abstractmethod
    def initialize_model(self) -> None:
        pass


    @abstractmethod
    def get_model_name(self) -> str:
        pass

    @abstractmethod
    def get_job_tag_generation_template(self) -> str:
        pass
