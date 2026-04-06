from app_v1.commons.service_logger import setup_logger
from app_v1.database.database_client import BaseDatabaseClient

from app_v1.database.database_models.job_notification_targets import JobNotificationTarget
from app_v1.database.tables import DatabaseTables
from app_v1.models.data_models.job_match_criteria import JobMatchCriteria
from app_v1.models.data_models.job_tag_response import JobTagResponse
from app_v1.models.data_models.user_interest import UserInterest
from app_v1.models.request_models.user_preference_request import UserPreferenceRequest

logger = setup_logger()

class JobNotificationTargetRepository:

    def __init__(self, database_client:BaseDatabaseClient):
        self._database_client:BaseDatabaseClient = database_client


    async def add_user_preferences(self, user_id:int, input_user_preference: UserPreferenceRequest) -> None:
        #TODO: update here
        query = f"""
            update {DatabaseTables.JOB_NOTIFICATION_TARGETS_TABLE.value} set
        """

        try:
            pass

        except Exception as exc:
            logger.error("Database error in add_user_preference", exc_info=True)
            raise

    async def remove_user_preferences(self, user_id:int, input_user_preferences: UserPreferenceRequest) -> None:
        #TODO: update here
        query = f"""
            update {DatabaseTables.JOB_NOTIFICATION_TARGETS_TABLE.value} set
        """

        try:
            pass

        except Exception as exc:
            logger.error("Database error in add_user_preference", exc_info=True)
            raise


    async def add_new_interest_row(self, job_match_criteria:JobMatchCriteria) -> None:
        query = f"""
            INSERT INTO {DatabaseTables.JOB_NOTIFICATION_TARGETS_TABLE.value} 
            (job_experience_level, job_location, company_name, user_ids)
            VALUES ($1, $2, $3, '{{}}'::INT[])
            ON CONFLICT (job_experience_level, job_location, company_name)
            DO NOTHING;
        """
        values = [
            job_match_criteria.job_experience_level.value,
            job_match_criteria.job_location,
            job_match_criteria.job_company_name
        ]
        try:
            await self._database_client.execute(query, *values)
        except Exception as exc:
            logger.error("Database error in add_new_interest_row", exc_info=True)
            raise

    async def get_job_notification_target_by_job_tags(self, job_tag_response: JobTagResponse) -> JobNotificationTarget | None:
        query = f"""
            SELECT * FROM {DatabaseTables.JOB_NOTIFICATION_TARGETS_TABLE.value}
            WHERE job_role_name = $1 AND job_location = $2 AND company_name = $3
        """

        try:
            row = await self._database_client.fetchrow(query, job_tag_response.job_role_name, job_tag_response.job_location, job_tag_response.job_company_name)
            if row is None:
                return None
            return JobNotificationTarget(**dict(row))

        except Exception as exc:
            logger.error("Database error in get_job_notification_target_by_job_tags", exc_info=True)
            raise
