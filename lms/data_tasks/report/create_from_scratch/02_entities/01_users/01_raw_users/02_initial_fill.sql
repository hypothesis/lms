DROP INDEX IF EXISTS report.raw_users_id_idx;

REFRESH MATERIALIZED VIEW report.raw_users;

ANALYSE report.raw_users;

-- A unique index is mandatory for concurrent updates used in the refresh
CREATE UNIQUE INDEX raw_users_id_idx ON report.raw_users (id);