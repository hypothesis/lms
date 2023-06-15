DROP INDEX IF EXISTS report.group_bubbled_type_counts_created_week_group_id_idx;

REFRESH MATERIALIZED VIEW report.group_bubbled_type_counts;

ANALYSE report.group_bubbled_type_counts;

-- A unique index is mandatory for concurrent updates used in the refresh
CREATE UNIQUE INDEX group_bubbled_type_counts_created_week_group_id_idx
    ON report.group_bubbled_type_counts (group_id, sub_type, shared, created_week);
