DROP INDEX IF EXISTS report.users_id_idx;
DROP INDEX IF EXISTS report.users_registered_date_idx;

REFRESH MATERIALIZED VIEW report.users;

ANALYSE report.users;

-- A unique index is mandatory for concurrent updates used in the refresh
CREATE UNIQUE INDEX users_id_idx ON report.users (id);
CREATE INDEX users_registered_date_idx ON report.users USING BRIN (registered_date);
