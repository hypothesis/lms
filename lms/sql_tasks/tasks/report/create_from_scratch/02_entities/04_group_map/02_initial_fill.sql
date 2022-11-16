DROP INDEX IF EXISTS report.group_map_lms_user_id_user_id_idx;

REFRESH MATERIALIZED VIEW report.group_map;

ANALYSE report.group_map;

-- A unique index is mandatory for concurrent updates used in the refresh
CREATE UNIQUE INDEX group_map_lms_grouping_id_user_id_idx ON report.group_map (lms_grouping_id, group_id);