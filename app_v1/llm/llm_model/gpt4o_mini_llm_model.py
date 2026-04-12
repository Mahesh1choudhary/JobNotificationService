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
             
        ### Input:
        - `job_description`: {job_description}
        
        ### Task
        Your task is analyze the given job description and extract following specific fields:
            - `job_role_name`: string -> Name of the job. Examples: SDE 1, SDE 2, Staff Engineer, Customer Success Manager, etc
                - Selected Job name should reflect the work done under the job.
                - Most of the time, job name is mentioned in `job_description`, select intelligently
            - `job_company_name` : string -> Name of the company offering the job
            - `job_type`: "Intern" | "FullTime" -> 
                - "Intern" if internship
                - "FullTime" if full-time roles
                
            - `job_experience_level`: reflects years of experience 
                - Decide based on minimum years of experience required for job and select as per below mapping
                    - ENTRY = if minimum year of experience required is in [0,2)
                    - JUNIOR = if minimum year of experience required is in [2,4)
                    - MID = if minimum year of experience required is in [4,6)
                    - SENIOR = if minimum year of experience required is in [6,10)
                    - EXPERT = if minimum year of experience required is 10+
                - If minimum years of experience is not mentioned, select and map intelligently
                - Steps to follow:
                    - First find the minimum year of experience required from the `job_description`. Now map this to only one of the available options
                    - Select only from the available options- ( ENTRY, JUNIOR, MID, SENIOR, EXPERT)
                    - Examples:
                        - If experience required is 5-6, then minimum year of experience is 5 which falls into Entry = [4,6) option
                        - If experience required is 12, then it falls into Expert = 10+ option 
            - `job_location`: string -> Location of the job. 
                - Should be city name, Country name or remote accordingly
            - `job_department`: string -> Department based on job work.
                - Decide based on responsibilities of the job
            - `job_link`: string | None -> link to the job
                - `job_description` may contains multiple different links, carefully select the one which points to the job
                - sometimes, there may not be job link info present in `job_description`
                    
            - `job_summary`: string -> 4-5 lines summary about the job
                - it should include
                    - Role responsibilities
                    - Tech stack (programming langauge, frameworks, databases, etc )
                    - years of experience ( if present)
        
        ### Strict Rules:
        - Output MUST be valid JSON. All keys must be present in output
        
        ### Output:
        {{
            "job_role_name": `job_role_name`,
            "job_company_name": `job_company_name`,
            "job_type": `job_type`,
            "job_experience_level": `job_experience_level`,
            "job_location": `job_location`,
            "job_department": `job_department`,
            "job_link": `job_link`,
            "job_summary": `job_summary`
        }}
        """