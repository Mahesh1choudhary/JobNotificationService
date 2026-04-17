import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn
import asyncio

from app_v1.commons.service_logger import setup_logger
from app_v1.database.database_config import DatabaseConfigFactory
from app_v1.database.database_manager import DatabaseManager
from app_v1.llm.llm_manager import LLMManager
from app_v1.llm.llm_model.embedding_model import EmbeddingModel
from app_v1.llm.llm_model.gpt4o_mini_llm_model import GPT4OMiniLLMModel
from app_v1.controller.user_controller import user_router
from app_v1.controller.user_preference_controller import user_preference_router
from app_v1.controller.ingestion_controller import ingestion_router
from app_v1.service.job_polling_service.job_polling_service import JobPollingService


logger = setup_logger()


def run_polling_in_background() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def initialize_and_start():
        llm_manager = LLMManager()
        llm_manager.set_tag_generation_model(GPT4OMiniLLMModel())
        llm_manager.set_embedding_model(EmbeddingModel())

        database_config = DatabaseConfigFactory.create_database_config()
        database_manager = DatabaseManager(database_config)
        await database_manager.init()

        try:
            service = JobPollingService(database_manager.database_client)
            await service.start_polling()
        finally:
            await database_manager.close()

    try:
        loop.run_until_complete(initialize_and_start())
    except Exception as e:
        logger.error(f"Background polling thread failed: {e}")
    finally:
        loop.close()


@asynccontextmanager
async def lifespan(app:FastAPI):
    # setting llm manager and creating database instance
    llm_manager = LLMManager()
    llm_manager.set_tag_generation_model(GPT4OMiniLLMModel())
    llm_manager.set_embedding_model(EmbeddingModel())

    database_config = DatabaseConfigFactory.create_database_config()
    database_manager = DatabaseManager(database_config)
    await database_manager.init()

    app.state.database_manager = database_manager #will be used in dependency injections

    #job polling moved to another thread's event loop to avoid delays in healthcheck and other api calls
    polling_thread = threading.Thread(target=run_polling_in_background,
                                      daemon=False)
    polling_thread.start()

    yield

    await database_manager.close()



def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.include_router(user_router)
    app.include_router(user_preference_router)
    app.include_router(ingestion_router)
    return app

def print_routes(app: FastAPI) -> None:
    print("Registered Routes:")
    for route in app.routes:
        print(f"Path: {getattr(route, 'path')}, Methods: {getattr(route, 'methods')}")

app = create_app()


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0"
    }


print_routes(app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008, reload=False)