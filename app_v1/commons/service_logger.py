import os
import logging
import threading
from logging.handlers import RotatingFileHandler
from typing import Optional

service_logger: Optional[logging.Logger] = None
_lock = threading.Lock()

def setup_logger():
    global service_logger

    if service_logger is None:
        with _lock:
            logger = logging.getLogger("Service_logger")
            logger.setLevel(logging.DEBUG)

            if not logger.handlers:
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

                is_local_env = os.getenv("ENV", "local") == "local"

                #TODO: can try QueueHandle for async logging or not multiple handlers; not needed as of now
                if is_local_env:
                    handler = logging.StreamHandler()
                else:
                    handler = RotatingFileHandler("service.log", maxBytes = 10**4, backupCount=2)

                handler.setLevel(logging.DEBUG)
                handler.setFormatter(formatter)
                logger.addHandler(handler)

            service_logger = logger
    return service_logger


service_logger = setup_logger()