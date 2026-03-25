

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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
--- by default index on user_id, user_name and email