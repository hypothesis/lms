ALTER SERVER "h_server" OPTIONS(
    SET host '{{h_fdw.host}}', -- SECRET
    SET port '{{h_fdw.port}}', 
    SET dbname '{{h_fdw.dbname}}'
);


ALTER USER MAPPING FOR "{{db_user}}" SERVER "h_server" OPTIONS(
    SET user '{{h_fdw.user}}',
    SET password '{{h_fdw.password}}' -- SECRET
);

DROP PROCEDURE IF EXISTS h.refresh_fdw_tables;
CREATE PROCEDURE h.refresh_fdw_tables(source_server text, target_schema text, table_names text[]) AS $$
DECLARE
    missing_tables text[] := (SELECT array_agg(fdw_tables) FROM  unnest(table_names) t("fdw_tables")
        WHERE fdw_tables NOT IN (
            -- Check which tables are already present
            -- otherwise IMPORT FOREIGN SCHEMA will raise
            SELECT table_name FROM "information_schema"."tables" WHERE table_schema = target_schema
        )
    );

BEGIN
    IF array_length(missing_tables, 1)  > 0 THEN
        execute 'IMPORT FOREIGN SCHEMA report LIMIT TO ('||  array_to_string(missing_tables, ',') ||') FROM SERVER '|| source_server || ' INTO ' || target_schema;
    END IF;
END;
$$ LANGUAGE PLPGSQL;

CALL h.refresh_fdw_tables(
    'h_server',
    'h',
    ARRAY[{{ h_fdw_tables|map('sql_literal')|join(",") }}]
);
