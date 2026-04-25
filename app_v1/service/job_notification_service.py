import re
from typing import List

from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

from app_v1.agent.tag_generation_agent import TagGenerationAgent
from app_v1.commons.service_logger import setup_logger
from app_v1.config.config_keys import SIMILARITY_THRESHOLD_FOR_VECTOR_SEARCH
from app_v1.config.config_loader import fetch_key_value
from app_v1.database.database_client import BaseDatabaseClient
from app_v1.database.database_config import DatabaseConfigFactory
from app_v1.database.database_manager import DatabaseManager
from app_v1.database.database_models.job_model import Job, JobProcessingStatus
from app_v1.database.repository.job_notification_target_repository import JobNotificationTargetRepository
from app_v1.database.repository.job_repository import JobRepository
from app_v1.llm.llm_manager import LLMManager
from app_v1.llm.llm_model.embedding_model import EmbeddingModel
from app_v1.llm.llm_model.gpt4o_mini_llm_model import GPT4OMiniLLMModel
from app_v1.models.data_models.job_match_criteria import JobMatchCriteria
from app_v1.models.data_models.job_tag_response import JobTagResponse
from app_v1.service.notification_service.notification_service import NotificationService
from app_v1.service.notification_service.notification_service_helpers.event_bus import EventBus
from app_v1.service.notification_service.notification_service_helpers.event_handlers import JobEventHandler
from app_v1.service.notification_service.notification_service_helpers.event_models import EventType, JobEvent
from app_v1.service.notification_service.notification_service_helpers.event_publishers import InMemoryEventPublisher
from app_v1.service.notification_service.notification_service_helpers.notification_payload import JobNotificationPayload
from app_v1.vector_data.job_company_name_namespace import JobCompanyNameNamespace
from app_v1.vector_data.job_department_name_namespace import JobDepartmentNameNamespace
from app_v1.vector_data.job_location_namespace import JobLocationNamespace
from app_v1.vector_data.vector_data_models.job_department_name_vector import JobDepartmentNameVector
from app_v1.vector_data.vector_data_models.job_location_vector import JobLocationVector

logger = setup_logger()


class JobNotificationService:
    # This is the main service

    def __init__(self, database_client:BaseDatabaseClient):
        self._agent = TagGenerationAgent()
        self._job_company_name_namespace = JobCompanyNameNamespace(database_client)
        self._job_location_namespace = JobLocationNamespace(database_client)
        self._job_department_name_namespace = JobDepartmentNameNamespace(database_client)
        self._job_notification_target_repository = JobNotificationTargetRepository(database_client)
        self._job_repository = JobRepository(database_client)
        self._similarity_threshold = fetch_key_value(SIMILARITY_THRESHOLD_FOR_VECTOR_SEARCH, float)

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

    async def generate_tags_and_send_notifications(self, job_data: Job) -> JobProcessingStatus:
        try:

            #TODO: temporary- to avoid llm cost. currently job is marked skipped when location , department, company, etc is not in table
            # so, adding prechecks to decide whether to process or not
            should_be_skipped: bool = await self.pre_filter_checks(job_data)
            if should_be_skipped:
                return JobProcessingStatus.SKIPPED

            raw_job_tag_response:JobTagResponse = await self.generate_tags(job_data.job_description)

            #TODO: job_data has company_id, so company name can come from there
            raw_job_tag_response.job_link = job_data.job_link
            job_company_name = await self._job_company_name_namespace.get_company_name_by_id(job_data.job_company_id) #TODO: it should be cached instead of db query every time
            if job_company_name is not None:
                raw_job_tag_response.job_company_name = job_company_name

            updated_job_tag_response, eligible_for_sending = await self.update_by_closest_matches(raw_job_tag_response)
            await self._job_repository.add_job_tag_responses(job_data.id, raw_job_tag_response, updated_job_tag_response)
            if not eligible_for_sending:
                return JobProcessingStatus.SKIPPED

            # adding combination row in interest/job_notification_target table- will be ignored if already present
            await self.add_new_interest_row(updated_job_tag_response)

            notification_payload = JobNotificationPayload(**updated_job_tag_response.model_dump())

            job_event = JobEvent(event_type=EventType.JOB_EVENT, job_tag_response=updated_job_tag_response, job_notification_payload= notification_payload)
            await self._event_publisher.publish(job_event)

            return JobProcessingStatus.PROCESSED
        except Exception as exc:
            logger.error("Error in generate_tags_and_send_notifications", exc_info=True)
            return JobProcessingStatus.PENDING

    async def update_by_closest_matches(self, job_tag_response:JobTagResponse) -> (JobTagResponse, bool):

        job_tag_response.job_company_name = job_tag_response.job_company_name.lower() # everthing should be in lower case
        #TODO: for now just for company_name and location, need to add for others. If best match is not found , will throw error
        best_match_job_company_names = await self._job_company_name_namespace.get_closest_matches(job_tag_response.job_company_name, self._similarity_threshold, 1)
        if not best_match_job_company_names:
            logger.warning(f"No best match found for company_name: {job_tag_response.job_company_name}")
            return job_tag_response, False
        job_tag_response.job_company_name = best_match_job_company_names[0].company_name

        job_tag_response.job_location = job_tag_response.job_location.lower()
        best_match_job_locations = await self._job_location_namespace.get_closest_matches(job_tag_response.job_location, self._similarity_threshold, 1)
        if not best_match_job_locations:
            logger.warning(f"No best match found for location: {job_tag_response.job_location}")
            return job_tag_response, False
        job_tag_response.job_location = best_match_job_locations[0].job_location


        job_tag_response.job_department = job_tag_response.job_department.lower()
        best_match_department_names = await self._job_department_name_namespace.get_closest_matches(job_tag_response.job_department, self._similarity_threshold, 1)
        if not best_match_department_names:
            logger.warning(f"No best match found for department: {job_tag_response.job_department}")
            return job_tag_response, False
        job_tag_response.job_department = best_match_department_names[0].department_name

        return job_tag_response, True


    async def add_new_interest_row(self, job_tag_response:JobTagResponse):
        job_match_criteria =  JobMatchCriteria(job_experience_level=job_tag_response.job_experience_level, job_location=job_tag_response.job_location,
                                               job_company_name=job_tag_response.job_company_name)
        await self._job_notification_target_repository.add_new_interest_row(job_match_criteria)



    async def pre_filter_checks(self, job_data:Job) -> bool:
        return False
        #TODO: for temporary use only
        try:
            job_description:str = job_data.job_description.strip()
            all_words = re.split(r'[ ,;.\n\t]+', job_description)
            word_set = set(all_words)
            normalized_word_set = {w.lower() for w in word_set}

            valid_locations:List[JobLocationVector] = await self._job_location_namespace.get_all_locations()

            location_set = set()
            for location in valid_locations:
                if location.job_location:
                    vals = re.split(r'[^a-zA-Z0-9]+', location.job_location.lower())
                    location_set.update(vals)

                if location.alias:
                    vals = re.split(r'[^a-zA-Z0-9]+', location.alias.lower())
                    location_set.update(vals)
            location_set.discard('')
            normalized_location_set = {w.lower() for w in location_set}

            location_matches = normalized_word_set.intersection(normalized_location_set)
            if not location_matches:
                return True


            valid_departments : List[JobDepartmentNameVector] = await self._job_department_name_namespace.get_all_departments()
            department_set = set()
            for department in valid_departments:
                if department.department_name:
                    vals = re.split(r'[^a-zA-Z0-9]+', department.department_name.lower())
                    department_set.update(vals)
            normalized_department_set = {w.lower() for w in department_set}

            department_matches = normalized_word_set.intersection(normalized_department_set)
            if not department_matches:
                return True

            return False
        except Exception as exc:
            logger.error("Error in pre_filter_checks", exc_info=True)
            return False


