

curl --location 'http://localhost:8008/ingestion/ingest' \
--header 'Content-Type: application/json' \
--data '{
"namespace_type": "job_company_namespace",
"data":[{
"company_name": "uber",
"description": ""
}]
}'

--- everything should be in lower case