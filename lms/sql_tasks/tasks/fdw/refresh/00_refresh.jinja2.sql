ALTER SERVER {{h_fdw_server_name}} OPTIONS(
    SET host '{{h_fdw_host}}',
    SET port '{{h_fdw_port}}',
    SET dbname '{{h_fdw_dbname}}'
);


ALTER USER MAPPING FOR {{db_user}} SERVER {{h_fdw_server_name}} OPTIONS(
    SET user '{{h_fdw_user}}',
    SET password '{{h_fdw_password}}'
);


-- Bring in any new tables from the server.
-- This won't delete any tables are are not longer declared in `h_fdw_tables`
{% for schema_name, table_name in h_fdw_tables %}
do
$$
BEGIN
    -- There's not `IF NOT EXISTS` for IMPORT FOREIGN SCHEMA, catch the execption in plpgsql
    IMPORT FOREIGN SCHEMA {{schema_name}} LIMIT TO ({{table_name}}) FROM SERVER {{h_fdw_server_name}} INTO h;
    EXCEPTION WHEN duplicate_table THEN  -- Nothing, we expected to find duplicates
END;
$$
language plpgsql;
{% endfor %}
