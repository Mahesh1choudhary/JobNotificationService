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

llm_manager = LLMManager()
logger = setup_logger()

class TagGenerationAgent(BaseChatAgent):


    async def on_messages(self,  messages: Sequence[BaseChatMessage], cancellation_token: CancellationToken):
        result = await self.generate_tags(messages)
        return Response(
            chat_message = TextMessage(content=result, source = self.name)
        )




    async def generate_tags(self, data: Sequence[BaseChatMessage]):

        llm_model: LLMModel = llm_manager.get_model()
        template = PromptTemplate(
            input_variables=["data"],
            template = llm_model.get_post_classification_template(),
        )
        prompt = template.format() #TODO: pass the content accordingly

        try:
            messages = [
                {"role":"system", "content": " you are a tag generation expert"},
                {"role":"user", "content": prompt}
            ]

            client = llm_model.initialize_model()
            result = await call_llm_with_retry(client= client, llm_model=llm_model, response_model=Response,
                                         messages=messages, agent_name = llm_model.get_model_name(), method_name = "classify")

            result_dict = result.model_dump()
            #TODO: extract required output
            return result_dict

        except Exception as exc:
            logger.error("Error generating tags with error: exc", exc_info=True)

