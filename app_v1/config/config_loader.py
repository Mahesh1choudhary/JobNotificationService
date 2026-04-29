import os, json
from pathlib import Path
from typing import Union, Type, TypeVar
from enum import Enum

from app_v1.commons.service_logger import setup_logger
from app_v1.config.config_classes_and_constants import EnvironmentConfigClass

logger = setup_logger()
T = TypeVar("T")

def fetch_key_value(key:Union[str,Enum], value_model: Type[T]) -> T:
    if isinstance(key, Enum):
        key= key.value

    env_type = os.getenv(EnvironmentConfigClass.ENV.value, "local")

    if env_type == "prod":
        env_val = os.getenv(key)
        if env_val is None:
            logger.error(f"Environment variable '{key}' not set")
            raise ValueError(f"Environment variable '{key}' not set.")
        try:
            result = json.loads(env_val)
        except json.JSONDecodeError:
            result = env_val
        if isinstance(result, dict):
            return value_model(**result)
        else:
            return value_model(result)
    else:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
        config_data_file_path = os.path.join(PROJECT_ROOT, "app_v1/config/config_data.json")

        if not os.path.exists(config_data_file_path):
            logger.error(f"{config_data_file_path} does not exist", exc_info=True)
            raise ValueError(f"config file for ENV:'{env_type}' not found at {config_data_file_path}.")

        with open(config_data_file_path, "r") as config_file:
            data = json.load(config_file) or {}

        try:
            result = data[key]
            if isinstance(result, dict):
                return value_model(**result)
            else:
                return value_model(result)
        except Exception as e:
            logger.error(f"Key: {key} not found in config_data_file_path", exc_info=True)
            raise ValueError(f"Key: {key} not found in config_data_file_path")