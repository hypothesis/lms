DROP INDEX IF EXISTS report.user_activity_created_week_user_id_idx;

REFRESH MATERIALIZED VIEW report.user_activity;

ANALYSE report.user_activity;

-- A unique index is mandatory for concurrent updates used in the refresh

CREATE UNIQUE INDEX user_activity_created_week_user_id_idx ON report.user_activity (created_week, user_id);