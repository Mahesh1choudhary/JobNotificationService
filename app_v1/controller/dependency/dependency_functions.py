from fastapi import Request

from app_v1.service.ingestion_service import IngestionService
from app_v1.service.user_preferences_service import UserPreferencesService
from app_v1.service.user_service import UserService
from app_v1.database.database_manager import DatabaseManager


def get_user_service(request: Request) -> UserService:
    database_manager: DatabaseManager = request.app.state.database_manager
    return UserService(database_manager.database_client)


def get_user_preferences_service(request:Request) -> UserPreferencesService:
    database_manager: DatabaseManager = request.app.state.database_manager
    return UserPreferencesService(database_manager.database_client)


def get_ingestion_service(request:Request) -> IngestionService:
    database_manager: DatabaseManager = request.app.state.database_manager
    return IngestionService(database_manager.database_client)


