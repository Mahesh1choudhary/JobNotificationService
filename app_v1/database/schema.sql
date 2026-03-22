

 --- companies table
CREATE TABLE IF NOT EXISTS companies (
    company_id SERIAL PRIMARY KEY,

    -- 'UNIQUE' automatically creates index
    company_name VARCHAR(255) UNIQUE NOT NULL,
    job_list_fetch_url TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
--- by default index on company_id and company_name