from app_v1.llm.llm_model.base_llm_model import LLMModel


class GPT51LLMModel(LLMModel):

    def __ini__(self):
        self.temperature: int =0
        self.llm_model_name: str = "gpt-5.1"
        self.time_out_seconds: int = 30

    def initialize_model(self):
        #TODO: update the initializaion logic
        api_key = ""
        if not api_key:
            raise ValueError("API key is not provided")

    def get_job_tag_generation_template(self) -> str:
        #TODO: update the prompt accordingly
        return """
        """