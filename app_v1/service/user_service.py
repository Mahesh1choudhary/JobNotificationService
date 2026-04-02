from app_v1.commons.service_logger import setup_logger
from app_v1.database.database_client import BaseDatabaseClient
from app_v1.database.database_models.user import User
from app_v1.database.repository.user_repository import UserRepository
from app_v1.models.request_models.user_creation_request import UserCreationRequest

logger = setup_logger()

class UserService():
    def __init__(self, database_client:BaseDatabaseClient):
        self._database_client = database_client
        self._user_repository = UserRepository(self._database_client)


    async def create_new_user(self, user_creation_request:UserCreationRequest):
        try:
            #TODO: should it be on user_name - in db, currently user_name made unique. Need to discuss
            existing_user:User = await self._user_repository.find_by_user_name(user_creation_request.user_name)
            if existing_user:
                raise ValueError(f"Username: {user_creation_request.user_name} already exists")
            new_user:User = await self._user_repository.save_user(user_creation_request)
            return new_user
        except Exception as exc:
            logger.error(f"Error in create_new_user", exc_info=True)
            raise
