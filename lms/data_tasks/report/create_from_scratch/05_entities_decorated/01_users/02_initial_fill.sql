DROP INDEX IF EXISTS report.users_id_idx;

REFRESH MATERIALIZED VIEW report.users;

ANALYSE report.users;

-- A unique index is mandatory for concurrent updates used in the refresh
CREATE UNIQUE INDEX users_id_idx ON report.users (id);
