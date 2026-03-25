from fastapi import APIRouter, Body, HTTPException, Depends
from typing import Annotated

from app_v1.commons.service_logger import setup_logger
from app_v1.service.user_service import UserCreationRequest, UserService
from app_v1.controller.dependency.dependency_functions import get_user_service

user_router = APIRouter(prefix="/user")
logger = setup_logger()


@user_router.post("/create", status_code=201)
async def create_user(user_creation_request: Annotated[UserCreationRequest, Body()],
                user_service: UserService = Depends(get_user_service)):
    try:
        await user_service.create_new_user(user_creation_request)
    except Exception as e:
        #TODO: proper error handling
        logger.error(f"Error in new user creation", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error")




