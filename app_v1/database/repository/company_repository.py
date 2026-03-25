from app_v1.commons.service_logger import setup_logger
from app_v1.database.database_client import BaseDatabaseClient
from app_v1.database.database_models.company import Company
from app_v1.database.tables import DatabaseTables

logger = setup_logger()

class CompanyRepository():

    def __init__(self, database_client:BaseDatabaseClient):
        self._database_client = database_client


    async def upsert_company(self, input_company_name: str, input_job_list_fetch_url) -> Company:
        query = f"""
        INSERT INTO {DatabaseTables.COMPANY_TABLE.value} (company_name, job_list_fetch_url)
        VALUES ($1, $2)
        ON CONFLICT (company_name)
        DO UPDATE SET job_list_fetch_url = EXCLUDED.job_list_fetch_url
        RETURNING company_id, company_name, job_list_fetch_url, created_at"""

        try:
            row = await self._database_client.fetchrow(query, input_company_name, input_job_list_fetch_url)
            return Company(**dict(row))
        except Exception as exc:
            logger.error(f"Database Error in upsert_company with company_name: {input_company_name}", exc_info=True)
            raise



    async def get_company_by_name(self, input_company_name: str) -> Company | None:
        query = f"SELECT * FROM {DatabaseTables.COMPANY_TABLE.value} WHERE company_name = $1"

        try:
            row = await self._database_client.fetchrow(query, input_company_name)
            return Company(**dict(row)) if row else None
        except Exception as exc:
            logger.error(f"Database Error in get_company_by_name with company_name: {input_company_name}", exc_info=True)
            raise
