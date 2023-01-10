DROP INDEX IF EXISTS report.users_sensitive_id_idx;

REFRESH MATERIALIZED VIEW report.users_sensitive;

ANALYSE report.users_sensitive;

-- A unique index is mandatory for concurrent updates used in the refresh
CREATE UNIQUE INDEX users_sensitive_id_idx ON report.users_sensitive (id);
