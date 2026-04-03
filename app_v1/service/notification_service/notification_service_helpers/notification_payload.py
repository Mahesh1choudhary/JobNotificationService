from abc import ABC

from app_v1.models.data_models.job_tag_response import JobType, JobTagResponse


class BaseNotificationPayload(ABC):
    pass


#TODO: will job link be part of JobTagResponse or need to separately add in JobNotidicationPayload
class JobNotificationPayload(JobTagResponse, BaseNotificationPayload):
    pass




