DROP INDEX IF EXISTS report.group_activity_created_week_group_id_idx;

REFRESH MATERIALIZED VIEW report.group_activity;

ANALYSE report.group_activity;

-- A unique index is mandatory for concurrent updates used in the refresh

CREATE UNIQUE INDEX group_activity_created_week_group_id_idx ON report.group_activity (created_week, group_id);