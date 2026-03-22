from abc import ABC, abstractmethod
from typing import Dict, ClassVar, Any, Type
from pydantic import BaseModel, ConfigDict

from app_v1.commons.service_logger import setup_logger
from app_v1.config.config_classes import DatabaseWrapperConfig
from app_v1.config.config_loader import fetch_key_value
from app_v1.config.config_keys import DATABASE_CONFIG_KEY

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

    postgresSQL_db_name: str
    postgresSQL_db_user: str
    postgresSQL_db_password: str
    postgresSQL_db_host: str
    postgresSQL_db_port: int
    postgresSQL_db_connection_pool_min:int = 2
    postgresSQL_db_connection_pool_max:int = 5

    model_config = ConfigDict(extra="forbid")  # no extra fields allowed



class DatabaseConfigFactory():

    _config_classes: Dict[str, Type[BaseDatabaseConfig]] = {
        PostgresSQLDatabaseConfig.get_database_name(): PostgresSQLDatabaseConfig,
    }

    @classmethod
    def create_database_config(cls) -> BaseDatabaseConfig:
        backend_database_config:DatabaseWrapperConfig = fetch_key_value(DATABASE_CONFIG_KEY, DatabaseWrapperConfig)
        backend_database_name:str = backend_database_config.database_name

        if backend_database_name not in cls._config_classes:
            available_backend_databases = ", ".join(cls._config_classes.keys())
            raise ValueError(f"Unknown backend database name provided: {backend_database_name}. Available databases: {available_backend_databases}")


        try:
            config_data = backend_database_config.database_config_data
            database_config: BaseDatabaseConfig = cls._config_classes[backend_database_name](**config_data)

            logger.info(f"Database config successfully created for {backend_database_name}")
            return database_config
        except Exception as exc:
            logger.error(f"Error creating database config: {exc}", exc_info=True)
            raise ValueError(f"Database config creation failed for database_name: {backend_database_name}, with error: {exc}")



