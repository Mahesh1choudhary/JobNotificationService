from pydantic import BaseModel
from typing import List

from app_v1.models.data_models.user_interest import UserInterest


class UserPreferenceRequest(BaseModel):
    preferences:List[UserInterest]
