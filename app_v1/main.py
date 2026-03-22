from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

from pathlib import Path
import logging
# call startup helper to ensure compressed resources exist
from startup import ensure_compressed  # type: ignore

from app_v1.database.database_config import BaseDatabaseConfig, DatabaseConfigFactory
from app_v1.database.database_manager import DatabaseManager
from app_v1.llm.llm_manager import LLMManager
from app_v1.llm.llm_model.gpt5_1_llm_model import GPT51LLMModel


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
    llm_manager.set_tag_generation_model(GPT51LLMModel)

    database_config = DatabaseConfigFactory.create_database_config()
    database_manager = DatabaseManager(database_config)
    await database_manager.init()

    app.state.database_manager = database_manager

    yield

    await database_manager.close()



def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    return app

def print_routes(app: FastAPI) -> None:
    print("Registered Routes:")
    for route in app.routes:
        print(f"Path: {getattr(route, 'path')}, Methods: {getattr(route, 'methods')}")

app = create_app()
print_routes(app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008, reload=False)