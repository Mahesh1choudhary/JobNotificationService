

---1 companies table
CREATE TABLE IF NOT EXISTS companies (
    company_id SERIAL PRIMARY KEY,

    -- 'UNIQUE' automatically creates index
    company_name VARCHAR(255) UNIQUE NOT NULL,
    job_list_fetch_url TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
--- by default index on company_id and company_name



---2 users table
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    user_name VARCHAR(255) UNIQUE NOT NULL,
    user_email VARCHAR(255) UNIQUE NOT NULL,
    user_telegram_user_name TEXT UNIQUE NOT NULL,
    user_telegram_chat_id BIGINT
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
--- by default index on user_id, user_name, user_telegram_user_name and email



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





---4 user quota table
CREATE TABLE IF NOT EXISTS user_quota (
    user_id INT PRIMARY KEY,
    total_count INT NOT NULL CHECK (total_count >= 0),
    used_count INT NOT NULL DEFAULT 0 CHECK (used_count >= 0)
    CHECK (used_count <= total_count)
)
--- by default index on user_id


-- enabling vector extension
CREATE EXTENSION IF NOT EXISTS vector;


--- Job company names vector table
CREATE TABLE IF NOT EXISTS job_company_names (
    id SERIAL PRIMARY KEY,
    company_name TEXT NOT NULL UNIQUE,
    description TEXT,
    embedding vector(1536)
)
CREATE INDEX ON job_company_names
USING hnsw(embedding vector_cosine_ops);
--- TODO: need to check other embeddings -> also currently using cosine rule, so when updated, update everwhere


--- Job locations vector table
CREATE TABLE IF NOT EXISTS job_locations (
    id SERIAL PRIMARY KEY,
    job_location TEXT NOT NULL UNIQUE,
    description TEXT,
    embedding vector(1536)
)
CREATE INDEX ON job_locations
USING hnsw (embedding vector_cosine_ops)