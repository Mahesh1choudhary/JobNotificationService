from abc import ABC, abstractmethod
import html

from app_v1.service.notification_service.notification_service_helpers.notification_payload import \
    BaseNotificationPayload, JobNotificationPayload


class NotificationRenderer(ABC):

    @abstractmethod
    def render(self, payload: BaseNotificationPayload) -> str:
        pass



class TelegramNotificationRenderer(NotificationRenderer):

    def render(self, payload: BaseNotificationPayload) -> str:
        if isinstance(payload, JobNotificationPayload):
            return (
                f"<b>Job Name :</b> {payload.job_role_name}\n"
                f"<b>Job Company Name :</b> {payload.job_company_name}\n"
                f"<b>Job Job Type :</b> {payload.job_type.value}\n"
                f"<b>Job Experience Level :</b> {payload.job_experience_level.value}\n"
                f"<b>Job Location :</b> {payload.job_location}\n"
                f"<b>Job Department :</b> {payload.job_department}\n"
                f"<b>Job Link :</b> {payload.job_link}\n"
                f"<b>Job Summary :</b> {html.escape(payload.job_summary)}"
            )
        else:
            raise ValueError(f"Render method not implemented for: {type(payload).__name__}")
