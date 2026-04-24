from typing import List

from app_v1.commons.service_logger import setup_logger
from app_v1.database.database_client import BaseDatabaseClient
from app_v1.database.database_models.company_job_source_model import CompanyJobSourceModel
from app_v1.database.tables import DatabaseTables

logger = setup_logger()

class CompaniesJobSourcesRepository():

    def __init__(self, database_client:BaseDatabaseClient):
        self._database_client = database_client

    async def insert_new_companies_job_sources(self, companies_job_sources_data:List[CompanyJobSourceModel]) -> None:
        query = f"""
            WITH input_data AS (
                SELECT * FROM unnest($1::text[], $2::text[], $3::jsonb[]) 
                AS t(c_name, p_name, f_config)
            ),
            inserted_rows AS (
                INSERT INTO {DatabaseTables.COMPANIES_JOB_SOURCES_TABLE.value} (company_id, platform_id, fetch_config)
                SELECT 
                    c.id, 
                    p.id, 
                    d.f_config
                FROM input_data d
                INNER JOIN {DatabaseTables.JOB_COMPANY_NAME_TABLE.value} c ON c.company_name = d.c_name
                INNER JOIN {DatabaseTables.JOB_PLATFORM_TABLE.value} p ON p.platform_name = d.p_name
                ON CONFLICT (company_id, platform_id) DO NOTHING
                RETURNING company_id, platform_id
            )
            -- This tells us which names we successfully matched and inserted
            SELECT c.company_name, p.platform_name 
            FROM inserted_rows i
            JOIN {DatabaseTables.JOB_COMPANY_NAME_TABLE.value} c ON c.id = i.company_id
            JOIN {DatabaseTables.JOB_PLATFORM_TABLE.value} p ON p.id = i.platform_id;
        """

        # Prepare arrays
        c_names = [s.company_name for s in companies_job_sources_data]
        p_names = [s.platform_name for s in companies_job_sources_data]
        configs = [s.fetch_config.model_dump() for s in companies_job_sources_data]

        try:
            # We use fetch instead of executemany to get the RETURNING data
            rows = await self._database_client.fetch(query, c_names, p_names, configs)

            inserted_set = {(r['company_name'], r['platform_name']) for r in rows}

            for source in companies_job_sources_data:
                if (source.company_name, source.platform_name) in inserted_set:
                    logger.info(f"INSERTED: {source.company_name} [{source.platform_name}]")

        except Exception as exc:
            logger.error("Database Error during batch insert with logging", exc_info=True)
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
