from abc import ABC

from app_v1.models.data_models.job_tag_response import JobType, JobTagResponse


class BaseNotificationPayload(ABC):
    pass


class JobNotificationPayload(JobTagResponse, BaseNotificationPayload):
    pass




