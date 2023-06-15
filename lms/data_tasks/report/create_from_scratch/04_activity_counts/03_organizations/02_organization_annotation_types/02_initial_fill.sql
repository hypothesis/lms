DROP INDEX IF EXISTS report.organization_annotation_types_period_timescale_sub_type_idx;
DROP INDEX IF EXISTS report.organization_annotation_types_start_date_end_date_idx;

REFRESH MATERIALIZED VIEW report.organization_annotation_types;

ANALYSE report.organization_annotation_types;

-- A unique index is mandatory for concurrent updates used in the refresh
CREATE UNIQUE INDEX organization_annotation_types_period_timescale_sub_type_idx
    ON report.organization_annotation_types (organization_id, timescale, sub_type, shared, period);
CREATE INDEX organization_annotation_types_start_date_end_date_idx
    ON report.organization_annotation_types (start_date, end_date);
