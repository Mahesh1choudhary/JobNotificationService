from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

from app_v1.agent.tag_generation_agent import TagGenerationAgent
from app_v1.commons.service_logger import setup_logger
from app_v1.database.database_client import BaseDatabaseClient
from app_v1.database.database_config import DatabaseConfigFactory
from app_v1.database.database_manager import DatabaseManager
from app_v1.llm.llm_manager import LLMManager
from app_v1.llm.llm_model.embedding_model import EmbeddingModel
from app_v1.llm.llm_model.gpt4o_mini_llm_model import GPT4OMiniLLMModel
from app_v1.models.data_models.job_tag_response import JobTagResponse
from app_v1.service.notification_service.notification_service import NotificationService
from app_v1.service.notification_service.notification_service_helpers.event_bus import EventBus
from app_v1.service.notification_service.notification_service_helpers.event_handlers import JobEventHandler
from app_v1.service.notification_service.notification_service_helpers.event_models import EventType, JobEvent
from app_v1.service.notification_service.notification_service_helpers.event_publishers import InMemoryEventPublisher
from app_v1.service.notification_service.notification_service_helpers.notification_payload import JobNotificationPayload
from app_v1.vector_data.job_company_name_namespace import JobCompanyNameNamespace
from app_v1.vector_data.job_location_namespace import JobLocationNamespace

logger = setup_logger()


class JobNotificationService:
    # This is the main service

    def __init__(self, database_client:BaseDatabaseClient):
        self._agent = TagGenerationAgent()
        self._job_company_name_namespace = JobCompanyNameNamespace(database_client)
        self._job_location_namespace = JobLocationNamespace(database_client)

        #TODO: in future all  handler, event bus setup,etc should be at a common separate place- maybe in fastapi lifespan
        #setting up handlers and event bus for job event
        handler = JobEventHandler(database_client)
        event_bus = EventBus()
        event_bus.register_handler(EventType.JOB_EVENT, handler)

        #setting up publisher
        self._event_publisher = InMemoryEventPublisher(event_bus) #TODO: for now in memory will be enough, in future, will think about using kafka or something else

    async def generate_tags(self, job_content: str) -> JobTagResponse:

        messages = [
            TextMessage(content=job_content, source="user")
        ]
        response = await self._agent.generate_tags(messages)
        response = response.model_dump()
        return JobTagResponse(**response)

    async def generate_tags_and_send_notifications(self, job_content: str):
        try:
            job_tag_response:JobTagResponse = await self.generate_tags(job_content)
            #TODO: how to generate job link -> from llm only or can get from job_content?

            job_tag_response = await self.update_by_closest_matches(job_tag_response)
            notification_payload = JobNotificationPayload(**job_tag_response.model_dump())

            job_event = JobEvent(event_type=EventType.JOB_EVENT, job_tag_response=job_tag_response, job_notification_payload= notification_payload)
            await self._event_publisher.publish(job_event)
        except Exception as exc:
            logger.error("Error in generate_tags_and_send_notifications", exc_info=True)
            raise

    async def update_by_closest_matches(self, job_tag_response:JobTagResponse) -> JobTagResponse:

        #TODO: for now just for company_name and location, need to add for others. If best match is not found , will throw error
        best_match_job_company_names = await self._job_company_name_namespace.get_closest_matches(job_tag_response.job_company_name.lower(), 1)
        if not best_match_job_company_names:
            raise ValueError(f"No best match found for company_name: {job_tag_response.job_company_name}")
        job_tag_response.job_company_name = best_match_job_company_names[0].company_name

        best_match_job_locations = await self._job_location_namespace.get_closest_matches(job_tag_response.job_location.lower(), 1)
        if not best_match_job_locations:
            raise ValueError(f"No best match found for location: {job_tag_response.job_location}")
        job_tag_response.job_location = best_match_job_locations[0].job_location.lower()

        return job_tag_response


