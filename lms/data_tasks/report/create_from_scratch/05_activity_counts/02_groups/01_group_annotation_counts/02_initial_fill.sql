DROP INDEX IF EXISTS report.group_annotation_counts_group_id_created_week_role_sub_type_idx;

REFRESH MATERIALIZED VIEW report.group_annotation_counts;

ANALYSE report.group_annotation_counts;

-- A unique index is mandatory for concurrent updates used in the refresh
CREATE UNIQUE INDEX group_annotation_counts_group_id_created_week_role_sub_type_idx
    ON report.group_annotation_counts (group_id, created_week, role, sub_type, shared);
