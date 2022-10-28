DROP SERVER IF EXISTS "{{h_fdw_server_name}}" CASCADE;

CREATE SERVER {{h_fdw_server_name}} FOREIGN DATA WRAPPER postgres_fdw 
    OPTIONS (host '{{h_fdw_host}}', port '{{h_fdw_port}}', dbname '{{h_fdw_dbname}}');

DROP USER MAPPING IF EXISTS FOR "{{db_user}}" SERVER "{{h_fdw_server_name}}";
CREATE USER MAPPING IF NOT EXISTS FOR "{{db_user}}"
    SERVER "{{h_fdw_server_name}}"
    OPTIONS (user '{{h_fdw_user}}', password '{{h_fdw_password}}');

DROP SCHEMA IF EXISTS h CASCADE;
-- Keep foreign tables on its own schema
CREATE SCHEMA h;

IMPORT FOREIGN SCHEMA "public" LIMIT TO (annotation) FROM SERVER "{{h_fdw_server_name}}" INTO h;
