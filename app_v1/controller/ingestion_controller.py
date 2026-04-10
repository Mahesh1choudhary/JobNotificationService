from typing import Annotated, List

from fastapi import APIRouter, Body, Depends, HTTPException

from app_v1.commons.service_logger import setup_logger
from app_v1.controller.dependency.dependency_functions import get_ingestion_service
from app_v1.models.request_models.ingestion_request import IngestionRequest, CompanyJobSourceIngestionRequest
from app_v1.models.request_models.user_creation_request import UserCreationRequest
from app_v1.service.ingestion_service import IngestionService

ingestion_router = APIRouter(prefix="/ingestion")

logger = setup_logger()

@ingestion_router.post('/ingest', status_code=200)
async def ingest_embedding_data(ingestion_request: Annotated[IngestionRequest, Body()],
                               ingestion_service: IngestionService = Depends(get_ingestion_service)):
    try:
        # for ingesting company_names and locations data only
        await ingestion_service.ingest_embedding_data_batch(ingestion_request)
        # await ingestion_service.ingest_embedding_data(ingestion_request)
    except Exception as e:
        #TODO: proper error handling
        logger.error(f"Error in data ingestion", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error")




@ingestion_router.post('/ingest_companies_job_sources', status_code=200)
async def ingest_companies_job_sources(ingestion_request: Annotated[List[CompanyJobSourceIngestionRequest], Body()],
                                       ingestion_service: IngestionService = Depends(get_ingestion_service)):
    try:
        # for ingesting companies job sources
        await ingestion_service.ingest_new_companies_job_sources(ingestion_request)
    except Exception as e:
        #TODO: proper error handling
        logger.error(f"Error in {ingest_companies_job_sources.__name__}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error")