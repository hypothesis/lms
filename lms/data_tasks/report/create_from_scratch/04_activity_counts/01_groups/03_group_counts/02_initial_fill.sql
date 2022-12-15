DROP INDEX IF EXISTS report.group_counts_group_id_idx;

REFRESH MATERIALIZED VIEW report.group_counts;

ANALYSE report.group_counts;

-- A unique index is mandatory for concurrent updates used in the refresh
CREATE UNIQUE INDEX group_counts_group_id_idx ON report.group_counts (group_id);
