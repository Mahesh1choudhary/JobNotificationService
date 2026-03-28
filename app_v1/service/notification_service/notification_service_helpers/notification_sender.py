import asyncio
from abc import ABC, abstractmethod
import httpx

from app_v1.commons.service_logger import setup_logger
from app_v1.config.config_keys import TELEGRAM_API_KEY
from app_v1.config.config_loader import fetch_key_value
from app_v1.database.database_models.user import User

logger = setup_logger()

class NotificationSender(ABC):
    @abstractmethod
    async def send_notification(self, user:User, notification_message:str):
        pass



class WhatsAppNotificationSender(NotificationSender):

    async def send_notification(self, user:User, notification_message:str):
        print(f"sending Whatsapp Notification to user")




class EmailNotificationSender(NotificationSender):
    async def send_notification(self, user:User, notification_message:str):
        print(f"sending Email Notification to user")


class TelegramNotificationSender(NotificationSender):

    def __init__(self):
        self.telegram_api_key = fetch_key_value(TELEGRAM_API_KEY, str)
        self.base_url = "https://api.telegram.org/bot" #TODO: should be config driven

    async def send_notification(self, user:User, notification_message:str):
        send_message_url = f"{self.base_url}{self.telegram_api_key}/sendMessage"

        #TODO:user needs to start conversation with the bot first-> then we have to save the chat_id received on the server.

        user_telegram_chat_id: int = user.user_telegram_chat_id
        if not user_telegram_chat_id:
            error_message:str = f"Cannot send Telegram Notification: user_telegram_chat_id is None for user: {user.user_name}"
            logger.error(error_message)
            raise ValueError(error_message)

        data = {
            "chat_id": user_telegram_chat_id,
            "text": notification_message
        }
