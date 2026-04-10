

-- job_platforms table
CREATE TABLE IF NOT EXISTS job_platforms (
    id SERIAL PRIMARY KEY,
    platform_name TEXT NOT NULL UNIQUE
);

----------------------------------------------------------------------------------

---1 companies table
CREATE TABLE IF NOT EXISTS companies_job_sources (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES job_company_names(id) ON DELETE CASCADE,
    platform_id INTEGER REFERENCES job_platforms(id),
    fetch_job_list_url TEXT NOT NULL,
    last_fetched_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT unique_source_per_company UNIQUE (company_id, platform_id, fetch_job_list_url)
);
--- by default index on company_id and company_name

----------------------------------------------------------------------------------

---2 users table
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    user_name VARCHAR(255) UNIQUE NOT NULL,
    user_email VARCHAR(255) UNIQUE NOT NULL,
    user_telegram_user_name TEXT UNIQUE NOT NULL,
    user_telegram_chat_id BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
--- by default index on user_id, user_name, user_telegram_user_name and email

----------------------------------------------------------------------------------

---3 job notification target table
CREATE TABLE IF NOT EXISTS job_notification_targets (
    id SERIAL PRIMARY KEY,
    job_experience_level TEXT NOT NULL,
    job_location TEXT NOT NULL,
    company_name TEXT NOT NULL,
    user_ids INT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- This constraint ensures only your Enum values can be inserted
    CONSTRAINT valid_experience_level CHECK (
    job_experience_level IN ('[0,2)', '[2-4)', '[4-6)', '[6-10)', '10+')
    ),

    -- Ensures we don't have duplicate targeting rules
    UNIQUE(job_experience_level, job_location, company_name)
);


----------------------------------------------------------------------------------


---4 user quota table
CREATE TABLE IF NOT EXISTS user_quota (
    user_id INT PRIMARY KEY,
    total_count INT NOT NULL CHECK (total_count >= 0),
    used_count INT NOT NULL DEFAULT 0 CHECK (used_count >= 0)
    CHECK (used_count <= total_count)
);
--- by default index on user_id


----------------------------------------------------------------------------------


-- enabling vector extension
CREATE EXTENSION IF NOT EXISTS vector;

----------------------------------------------------------------------------------

--- Job company names vector table
CREATE TABLE IF NOT EXISTS job_company_names (
    id SERIAL PRIMARY KEY,
    company_name TEXT NOT NULL UNIQUE,
    description TEXT,
    embedding vector(1536),

    fts_tokens tsvector GENERATED ALWAYS AS (
    to_tsvector('english', company_name || ' ' || coalesce(description, ''))
    ) STORED
);
CREATE INDEX ON job_company_names
USING hnsw(embedding vector_cosine_ops);
--- TODO: need to check other embeddings -> also currently using cosine rule, so when updated, update everwhere

-- full text search index( GIN)
CREATE INDEX idx_job_company_names_fts ON job_company_names USING GIN (fts_tokens);


----------------------------------------------------------------------------------


--- Job locations vector table
CREATE TABLE IF NOT EXISTS job_locations (
    id SERIAL PRIMARY KEY,
    job_location TEXT NOT NULL UNIQUE,
    description TEXT,
    embedding vector(1536),

    fts_tokens tsvector GENERATED ALWAYS AS (
        to_tsvector('english', job_location || ' ' || coalesce(description, ''))
        ) STORED
);
-- vector index
CREATE INDEX ON job_locations USING hnsw (embedding vector_cosine_ops);

-- full text search index( GIN)
CREATE INDEX idx_job_locations_fts ON job_locations USING GIN (fts_tokens);



----------------------------------------------------------------------------------


--- Job department vector table
CREATE TABLE IF NOT EXISTS job_departments (
   id SERIAL PRIMARY KEY,
   department_name TEXT NOT NULL UNIQUE,
   description TEXT,
   embedding vector(1536),

   fts_tokens tsvector GENERATED ALWAYS AS (
       to_tsvector('english', department_name || ' ' || coalesce(description, ''))
       ) STORED
);
CREATE INDEX ON job_departments
USING hnsw (embedding vector_cosine_ops);

-- full text search index( GIN)
CREATE INDEX idx_job_departments_fts ON job_departments USING GIN (fts_tokens);


----------------------------------------------------------------------------------

--- Jobs table
CREATE TABLE jobs (
  id SERIAL PRIMARY KEY,
  job_company_id INTEGER NOT NULL,
  job_link TEXT,
  job_description TEXT NOT NULL,
  job_description_hash TEXT,
  job_processing_status TEXT NOT NULL DEFAULT 'pending'
      CHECK (job_processing_status IN ('pending', 'processed', 'skipped')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

  UNIQUE(job_company_id, job_link, job_description_hash)
);

----------------------------------------------------------------------------------
