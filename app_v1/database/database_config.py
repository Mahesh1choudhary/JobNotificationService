from abc import ABC, abstractmethod
from typing import Dict, ClassVar, Any, Type
from pydantic import BaseModel, ConfigDict

from app_v1.commons.service_logger import setup_logger

logger = setup_logger()

class BaseDatabaseConfig(BaseModel, ABC):
    _backend_database_name: ClassVar[str] = None

    @classmethod
    @abstractmethod
    def get_database_name(cls) -> str:
        return cls._backend_database_name


class PostgresSQLDatabaseConfig(BaseDatabaseConfig):
    _backend_database_name: ClassVar[str] = "postgresSQL"

    @classmethod
    def get_database_name(cls) -> str:
        return cls._backend_database_name

    #TODO: should be config driven
    postgresSQL_db_name: str
    postgresSQL_db_user: str
    postgresSQL_db_password: str
    postgresSQL_db_host: str
    postgresSQL_db_port: str

    batch_size: int = 5000
    max_workers: int = 10
    postgresSQL_db_connection_pool_min:int = 2
    postgresSQL_db_connection_pool_max:int = 5

    model_config = ConfigDict(extra="forbid")  # no extra fields allowed




class DatabaseConfigFactory():

    _config_classes: Dict[str, Type[BaseDatabaseConfig]] = {
        PostgresSQLDatabaseConfig.get_database_name(): PostgresSQLDatabaseConfig,
    }

    @classmethod
    def create_database_config(cls) -> BaseDatabaseConfig:
        backend_database_name:str = "postgresSQL" #TODO: fetch from config only along with config_data

        if backend_database_name not in cls._config_classes:
            available_backend_databases = ", ".join(cls._config_classes.keys())
            raise ValueError(f"Unknown backend database name provided: {backend_database_name}. Available databases: {available_backend_databases}")


        try:
            config_data: Dict[str, Any]= {
                "postgresSQL_db_name": "name",
                "postgresSQL_db_user": "user",
                "postgresSQL_db_password": "password",
                "postgresSQL_db_host": "host",
                "postgresSQL_db_port": "0000"
            }
            database_config: BaseDatabaseConfig = cls._config_classes[backend_database_name](**config_data)

            logger.info(f"Database config successfully created for {backend_database_name}")
            return database_config
        except Exception as exc:
            logger.error(f"Error creating database config: {exc}", exc_info=True)
            raise ValueError(f"Database config creation failed for database_name: {backend_database_name}, with error: {exc}")



