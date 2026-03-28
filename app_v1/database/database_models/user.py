from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class User(BaseModel):
    user_id: Optional[int]
    user_name: str
    user_email: str
    user_telegram_user_name:str #TODO: In future, create separate table for user_contacts. Need to discuss on this
    user_telegram_chat_id: int | None = None
    created_at: Optional[datetime]
    updated_at: Optional[datetime]