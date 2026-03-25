from fastapi import Request

from app_v1.service.user_service import UserService
from app_v1.database.database_manager import DatabaseManager


def get_user_service(request: Request) -> UserService:
    database_manager: DatabaseManager = request.app.state.database_manager
    return UserService(database_manager.database_client)

