from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

from app_v1.agent.tag_generation_agent import TagGenerationAgent
from app_v1.models.data_models.job_tag_response import JobTagResponse


class TagGenerationService:

    def __init__(self, agent: TagGenerationAgent):
        self._agent = agent

    async def generate_tags(self, job_content: str) -> JobTagResponse:

        messages = [
            TextMessage(content=job_content, source="user")
        ]
        response = await self._agent.generate_tags(messages)
        response = response.model_dump()
        return JobTagResponse(**response)

