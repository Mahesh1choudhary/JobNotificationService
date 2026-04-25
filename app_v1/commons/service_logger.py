import os
import logging
import threading
from logging.handlers import RotatingFileHandler
from typing import Optional

service_logger: Optional[logging.Logger] = None
_thread_lock = threading.Lock()

def setup_logger():
    global service_logger

    if service_logger is None:
        with _thread_lock:
            if service_logger is not None:
                return service_logger

            logger = logging.getLogger("Service_logger")
            logger.setLevel(logging.ERROR)

            if not logger.handlers:
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

                # same for prod and local
                handler = logging.StreamHandler()


                handler.setLevel(logging.ERROR)
                handler.setFormatter(formatter)
                logger.addHandler(handler)

            service_logger = logger
    return service_logger


service_logger = setup_logger()