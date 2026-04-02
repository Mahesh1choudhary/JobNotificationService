import asyncio
from abc import ABC, abstractmethod
import httpx

from app_v1.commons.service_logger import setup_logger
from app_v1.config.config_keys import TELEGRAM_API_KEY
from app_v1.config.config_loader import fetch_key_value
from app_v1.database.database_models.user import User
from app_v1.service.notification_service.notification_service_helpers.notification_payload import \
    BaseNotificationPayload
from app_v1.service.notification_service.notification_service_helpers.notification_payload_renderer import \
    TelegramNotificationRenderer

logger = setup_logger()

class NotificationSender(ABC):
    @abstractmethod
    async def send_notification(self, user:User, notification_payload:BaseNotificationPayload):
        pass



class WhatsAppNotificationSender(NotificationSender):

    async def send_notification(self, user:User, notification_message:BaseNotificationPayload):
        print(f"sending Whatsapp Notification to user")




class EmailNotificationSender(NotificationSender):
    async def send_notification(self, user:User, notification_message:BaseNotificationPayload):
        print(f"sending Email Notification to user")


class TelegramNotificationSender(NotificationSender):

    def __init__(self):
        self._telegram_api_key = fetch_key_value(TELEGRAM_API_KEY, str)
        self._base_url = "https://api.telegram.org/bot" #TODO: should be config driven
        self._notification_renderer = TelegramNotificationRenderer()

    async def send_notification(self, user:User, notification_message:BaseNotificationPayload):
        send_message_url = f"{self._base_url}{self._telegram_api_key}/sendMessage"

        #TODO:user needs to start conversation with the bot first-> then we have to save the chat_id received on the server.

        user_telegram_chat_id: int = user.user_telegram_chat_id
        if not user_telegram_chat_id:
            error_message:str = f"Cannot send Telegram Notification: user_telegram_chat_id is None for user: {user.user_name}"
            logger.error(error_message)
            raise ValueError(error_message)

        rendered_notification_message = self._notification_renderer.render(notification_message)
        data = {
            "chat_id": user_telegram_chat_id,
            "text": rendered_notification_message,
            "parse_mode": "HTML"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(send_message_url, json=data)
                response.raise_for_status()
            except Exception as exc:
                logger.error("Error sending Telegram Notification", exc_info=True)
                raise


    async def check_for_new_registrations(self):
        #TODO: if some new user start chat with the bot, then need to update the chat id in the database
        get_updates_url = f"{self._base_url}{self._telegram_api_key}/getUpdates"
        offset= -1
        params = {"offset":0}
        async with httpx.AsyncClient() as client:
            response = await client.get(get_updates_url, params=params)
            updates= response.json().get("result", [])
            for update in updates:
               print(f"new registered user: {update}")