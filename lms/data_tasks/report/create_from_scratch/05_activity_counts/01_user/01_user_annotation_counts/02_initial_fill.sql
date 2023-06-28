DROP INDEX IF EXISTS report.user_annotation_counts_user_id_group_id_created_week_idx;

REFRESH MATERIALIZED VIEW report.user_annotation_counts;

ANALYSE report.user_annotation_counts;

-- A unique index is mandatory for concurrent updates used in the refresh
CREATE UNIQUE INDEX user_annotation_counts_user_id_group_id_created_week_idx
    ON report.user_annotation_counts (user_id, group_id, created_week, sub_type, shared);
