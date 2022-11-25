DROP INDEX IF EXISTS report.user_map_lms_user_id_user_id_idx;

REFRESH MATERIALIZED VIEW report.user_map;

ANALYSE report.user_map;

-- A unique index is mandatory for concurrent updates used in the refresh
CREATE UNIQUE INDEX user_map_lms_user_id_user_id_idx ON report.user_map (lms_user_id, user_id);
