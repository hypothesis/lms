-- In production this must have been either 
-- provisioned while creating the RDS db or run with and admin user
-- before this task can run successfully
CREATE EXTENSION IF NOT EXISTS postgres_fdw;

DROP SERVER IF EXISTS "h_server" CASCADE;
CREATE SERVER "h_server" FOREIGN DATA WRAPPER postgres_fdw
    OPTIONS (
        host '{{h_fdw.host}}', -- SECRET
        port '{{h_fdw.port}}', 
        dbname '{{h_fdw.dbname}}'
);

DROP USER MAPPING IF EXISTS FOR "{{db_user}}" SERVER "h_server";
CREATE USER MAPPING IF NOT EXISTS FOR "{{db_user}}"
    SERVER "h_server"
    OPTIONS (
        user '{{h_fdw.user}}',
        password '{{h_fdw.password}}' -- SECRET
);


DROP SCHEMA IF EXISTS h CASCADE;
-- Keep foreign tables on its own schema
CREATE SCHEMA h;

IMPORT FOREIGN SCHEMA "report" LIMIT TO (
    "authorities",
    "annotation_group_counts",
    "annotation_user_counts"
) FROM SERVER "h_server" INTO h;
