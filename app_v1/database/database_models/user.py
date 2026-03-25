from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class User(BaseModel):
    user_id: Optional[int]
    user_name: str
    user_email: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]