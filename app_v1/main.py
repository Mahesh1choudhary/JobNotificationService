import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

from app_v1.database.database_config import DatabaseConfigFactory
from pathlib import Path
import logging

from app_v1.commons.service_logger import setup_logger
# call startup helper to ensure compressed resources exist
from startup import ensure_compressed  # type: ignore

from app_v1.database.database_config import DatabaseConfigFactory
from app_v1.database.database_manager import DatabaseManager
from app_v1.llm.llm_manager import LLMManager
from app_v1.llm.llm_model.gpt4o_mini_llm_model import GPT4OMiniLLMModel
from app_v1.controller.user_controller import user_router
from app_v1.database.repository.job_repository import JobRepository
from app_v1.service.greenhouse_job_polling_service import (
    GreenhouseJobPollingService,
    poll_interval_from_env,
    polling_enabled_from_env,
)

logger = setup_logger()

@asynccontextmanager
async def lifespan(app:FastAPI):
    # ensure compressed greenhouse JSON exists before initializing other services
    try:
        resources_dir = Path(__file__).resolve().parent / "resources"
        print(resources_dir)
        ensure_compressed(resources_dir=resources_dir)

    except Exception:
        logging.exception("ensure_compressed failed during app startup; continuing startup.")

    # setting llm manager and creating database instance
    llm_manager = LLMManager()
    llm_manager.set_tag_generation_model(GPT4OMiniLLMModel())

    database_config = DatabaseConfigFactory.create_database_config()
    database_manager = DatabaseManager(database_config)
    await database_manager.init()

    app.state.database_manager = database_manager #will be used in dependency injections

    poll_task: asyncio.Task | None = None
    if True:
        resources_dir = Path(__file__).resolve().parent / "resources"
        compressed_path = resources_dir / "greenhouse_clients_compressed.json"
        logger.info(compressed_path)
        job_repo = JobRepository(database_manager.database_client)
        poller = GreenhouseJobPollingService(
            job_repo,
            compressed_json_path=compressed_path,
            poll_interval_seconds=poll_interval_from_env(),
        )
        poll_task = asyncio.create_task(poller.run_forever())
        logger.info("Created task for polling")
        app.state.greenhouse_poll_task = poll_task

    yield

    if poll_task is not None:
        poll_task.cancel()
        try:
            await poll_task
        except asyncio.CancelledError:
            pass

    await database_manager.close()



def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.include_router(user_router)
    return app

def print_routes(app: FastAPI) -> None:
    print("Registered Routes:")
    for route in app.routes:
        print(f"Path: {getattr(route, 'path')}, Methods: {getattr(route, 'methods')}")

app = create_app()
print_routes(app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008, reload=False)