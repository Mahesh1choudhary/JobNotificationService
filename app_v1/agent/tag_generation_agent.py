from logging import getLogger
from typing import Sequence
from autogen_agentchat.agents import BaseChatAgent
from autogen_agentchat.base import Response
from autogen_agentchat.messages import BaseChatMessage, TextMessage
from autogen_core import CancellationToken

from langchain_core.prompts import PromptTemplate

from app_v1.llm.helpers import call_llm_with_retry
from app_v1.llm.llm_manager import LLMManager
from app_v1.llm.llm_model.base_llm_model import LLMModel
from app_v1.commons.service_logger import setup_logger
from app_v1.models.data_models.job_tag_response import JobTagResponse

llm_manager = LLMManager()
logger = setup_logger()

class TagGenerationAgent(BaseChatAgent):

    def __init__(self):
        self._agent_name = "TagGenerationAgent"
        self._description = "An agent that extracts technical tags from job descriptions."
        super().__init__(name= self._agent_name, description=self._description)


    async def on_messages(self,  messages: Sequence[BaseChatMessage], cancellation_token: CancellationToken):
        result = await self.generate_tags(messages)
        json_result = result.model_dump_json()
        return Response(
            chat_message = TextMessage(content=json_result, source = self.name)
        )


    async def generate_tags(self, job_description: Sequence[BaseChatMessage]) -> JobTagResponse:

        llm_model: LLMModel = llm_manager.get_tag_generation_model()
        template = PromptTemplate(
            input_variables=["job_description"],
            template = llm_model.get_job_tag_generation_template(),
        )
        prompt = template.format(job_description = job_description)

        try:
            messages = [
                {"role":"system", "content": " you are a tag generation expert"},
                {"role":"user", "content": prompt}
            ]

            client = llm_model.initialize_model()
            result:JobTagResponse = await call_llm_with_retry(client= client, llm_model=llm_model, response_model=JobTagResponse,
                                         messages=messages, agent_name = llm_model.get_model_name(), method_name = "generate_tags")

            return result

        except Exception as exc:
            logger.error("Error generating tags", exc_info=True)
            raise

    def produced_message_types(self) -> Sequence[type[BaseChatMessage]]:
        pass

    async def on_reset(self, cancellation_token: CancellationToken) -> None:
        pass