from pydantic import BaseModel


class UserQuota(BaseModel):
    user_id:int
    total_count: int
    used_count: int