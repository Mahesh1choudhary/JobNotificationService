from pydantic import BaseModel, Field, EmailStr


class UserCreationRequest(BaseModel):
    user_name:str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    user_email:EmailStr
    user_telegram_user_name:str = Field(..., min_length=1, max_length=200)