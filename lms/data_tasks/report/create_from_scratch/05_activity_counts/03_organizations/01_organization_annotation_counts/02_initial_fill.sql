DROP INDEX IF EXISTS report.organization_annotation_counts_period_timescale_role_idx;
DROP INDEX IF EXISTS report.organization_annotation_counts_start_date_end_date_idx;

REFRESH MATERIALIZED VIEW report.organization_annotation_counts;

ANALYSE report.organization_annotation_counts;

-- A unique index is mandatory for concurrent updates used in the refresh
CREATE UNIQUE INDEX organization_annotation_counts_period_timescale_role_idx
    ON report.organization_annotation_counts (organization_id, timescale, role, sub_type, shared, period);
CREATE INDEX organization_annotation_counts_start_date_end_date_idx
    ON report.organization_annotation_counts (start_date, end_date);
