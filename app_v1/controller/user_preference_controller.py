from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException

from app_v1.commons.service_logger import setup_logger
from app_v1.controller.dependency.dependency_functions import get_user_preferences_service
from app_v1.models.request_models.user_preference_request import UserPreferenceRequest
from app_v1.service.user_preferences_service import UserPreferencesService

user_preference_router = APIRouter(prefix="/user_preferences")
logger = setup_logger()

user_preference_router.post("/add_preferences")
async def add_user_preferences(user_preferences: Annotated[UserPreferenceRequest, Body()],
                               user_preferences_service: UserPreferencesService = Depends(get_user_preferences_service)):

    try:
        result = await user_preferences_service.add_user_preferences(user_preferences)
        return result

    except Exception as exc:
        logger.error("Error in add_user_preferences", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error")


user_preference_router.post("/remove_preferences")
async def remove_user_preferences(user_preferences: Annotated[UserPreferenceRequest, Body()],
                                  user_preferences_service: UserPreferencesService = Depends(get_user_preferences_service)):
    try:
        result = await user_preferences_service.remove_user_preferences(user_preferences)
        return result

    except Exception as exc:
        logger.error("Error in remove_user_preferences", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error")

    #TODO: proper error handling