from typing import List

from app_v1.commons.service_logger import setup_logger
from app_v1.database.database_client import BaseDatabaseClient
from app_v1.database.database_models.company_job_source_model import CompanyJobSourceModel
from app_v1.database.tables import DatabaseTables

logger = setup_logger()

class CompaniesJobSourcesRepository():

    def __init__(self, database_client:BaseDatabaseClient):
        self._database_client = database_client

    async def insert_new_company_job_source(self, company_job_source_data:CompanyJobSourceModel) -> None:
        query = f"""
            WITH company_name_table AS (
            SELECT id FROM {DatabaseTables.JOB_COMPANY_NAME_TABLE.value} WHERE company_name = $1
            ),
            platform_table AS (
                SELECT id FROM {DatabaseTables.JOB_PLATFORM_TABLE.value} WHERE platform_name = $2
            )
            INSERT INTO {DatabaseTables.COMPANIES_JOB_SOURCES_TABLE.value} 
                (company_id, platform_id, fetch_config)
            SELECT company_name_table.id, platform_table.id, $3
            FROM company_name_table, platform_table
            ON CONFLICT (company_id, platform_id) 
            DO NOTHING
        """

        try:
            logger.info(f"[{self.__class__.__name__}]-[{self.insert_new_company_job_source.__name__}]: inserting new company_job_source : {company_job_source_data}")
            #TODO: should log whether row is added or not
            await self._database_client.execute(query, company_job_source_data.company_name, company_job_source_data.platform_name,
                                                company_job_source_data.fetch_config.model_dump())
        except Exception as exc:
            logger.error(f"[{self.__class__.__name__}]-[{self.insert_new_company_job_source.__name__}]: Database Error while inserting company_job_source : {company_job_source_data}", exc_info=True)
            raise

    async def update_company_job_source_last_fetched_at(self, company_job_source_data:CompanyJobSourceModel) -> None:
        query = f"""
            UPDATE  {DatabaseTables.COMPANIES_JOB_SOURCES_TABLE.value}
            SET last_fetched_at = $3
            where company_id = $1 and platform_id = $2
        """
        try:
            logger.info(f"[{self.__class__.__name__}]-[{self.update_company_job_source_last_fetched_at.__name__}]: updating last_fetched_at for company_job_source: {company_job_source_data}")
            await self._database_client.execute(query, company_job_source_data.company_id, company_job_source_data.platform_id,
                                                company_job_source_data.last_fetched_at)
        except Exception as exc:
            logger.error(f"[{self.__class__.__name__}]-[{self.update_company_job_source_last_fetched_at.__name__}]: Database Error while updating last_fetched_at for company_job_source: {company_job_source_data}", exc_info=True)
            raise

    async def get_active_companies_job_source_data(self, offset:int, limit:int) -> List[CompanyJobSourceModel]:
        query = f"""
            SELECT  cjs.id, cjs.company_id, cjs.platform_id, cjs.fetch_config, cjs.last_fetched_at,
             jp.platform_name, jcn.company_name
            FROM {DatabaseTables.COMPANIES_JOB_SOURCES_TABLE.value} cjs
            JOIN
            {DatabaseTables.JOB_PLATFORM_TABLE.value} jp
                ON cjs.platform_id = jp.id
            JOIN {DatabaseTables.JOB_COMPANY_NAME_TABLE.value} jcn
                ON cjs.company_id = jcn.id
            WHERE cjs.is_active=True
            ORDER BY cjs.id
            OFFSET $1 LIMIT $2
        """

        try:
            logger.info(f"[{self.__class__.__name__}]-[{self.get_active_companies_job_source_data.__name__}]: getting data for offset: {offset}, limit: {limit}")
            rows = await self._database_client.fetch(query, offset, limit)
            return [CompanyJobSourceModel(**dict(row)) for row in rows]
        except Exception as exc:
            logger.error(f"[{self.__class__.__name__}]-[{self.get_active_companies_job_source_data.__name__}]: database error", exc_info=True)
            raise


    async def get_total_entries_count(self) -> int:
        query = f"""
            SELECT COUNT(*) FROM {DatabaseTables.COMPANIES_JOB_SOURCES_TABLE.value}
        """
        try:
            logger.info(f"[{self.__class__.__name__}]-[{self.get_total_entries_count.__name__}]: getting total number of companies jobs sources data")
            row = await self._database_client.fetchrow(query)
            return row[0] if row else 0
        except Exception as exc:
            logger.error(f"[{self.__class__.__name__}]-[{self.get_total_entries_count.__name__}]: Database Error in get_total_entries_count", exc_info=True)
            raise
