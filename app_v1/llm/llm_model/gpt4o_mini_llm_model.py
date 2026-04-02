import instructor
from openai import AsyncOpenAI

from app_v1.commons.service_logger import setup_logger
from app_v1.config.config_keys import OPENAI_API_KEY
from app_v1.config.config_loader import fetch_key_value
from app_v1.llm.llm_model.base_llm_model import LLMModel

logger = setup_logger()

class GPT4OMiniLLMModel(LLMModel):

    def __init__(self):
        self.temperature: int =0
        self.llm_model_name: str = "gpt-4o-mini"
        self.time_out_seconds: int = 30

    def get_model_name(self) -> str:
        return self.llm_model_name

    def initialize_model(self):
        try:
            open_api_key = fetch_key_value(OPENAI_API_KEY, str)
            if not open_api_key:
                raise ValueError("API key is not provided")
            client = instructor.patch(AsyncOpenAI(api_key=open_api_key))
            return client
        except Exception as e:
            logger.error(f"Error initializing {self.get_model_name()}", exc_info=True)
            raise

    def get_job_tag_generation_template(self) -> str:
        return """
        ### Role
        You are expert at extracting structured job information from the job description.
        
        ### Task
        Your task is analyze the given job description and extract specific fields:
            - `job_company_name` : string -> Name of the company offering the job
            - `job_experience_level`: "Intern" | "FullTime" -> 
                - "Intern" if internship
                - "FullTime" if full-time roles
            - `job_location`: string -> Location of the job. Should be city name, Country name or remote if applicable
            - `job_department`: string -> Department based on job work. Examples- Engineering, Sales, Finance, etc
            - `job_role_name`: string -> Name of the job. Examples: SDE 1, SDE 2, Staff Engineer, Customer Success Manager, etc
            - `job_summary`: string -> 4-5 lines summary about the job
                - It should include info about the tech stack if present in job description: programming langauges, frameworks, databases, etc
                - It should contain year of experience if present in job description
            
        ### Input:
        - `job_description`: {job_description}
        
        ### Rules:
        - Return ***valid JSON***. All keys must be present in output
        - No key should be ull, choose the best possible value
        
        ### Output:
        {{
            "job_company_name": `job_company_name`,
            "job_experience_level": `job_experience_level`,
            "job_location": `job_location`,
            "job_department": `job_department`,
            "job_role_name": `job_role_name`,
            "job_summary": `job_summary`
        }}
        """