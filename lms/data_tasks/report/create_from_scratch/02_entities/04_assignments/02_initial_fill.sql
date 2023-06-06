DROP INDEX IF EXISTS report.assignments_id_idx;

REFRESH MATERIALIZED VIEW report.assignments;

ANALYSE report.assignments;

-- A unique index is mandatory for concurrent updates used in the refresh
CREATE UNIQUE INDEX assignments_id_idx ON report.assignments (id);
