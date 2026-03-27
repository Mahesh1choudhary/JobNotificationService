from datetime import datetime
from pydantic import BaseModel

from app_v1.models.data_models.user_interest import UserInterest


class UserPreference(BaseModel):
    user_id: int
    preferences: list[UserInterest]
    created_at: datetime
    updated_at: datetime
