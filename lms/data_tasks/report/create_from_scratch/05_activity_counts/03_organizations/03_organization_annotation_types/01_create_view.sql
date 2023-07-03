DROP VIEW IF EXISTS report.organization_annotation_types CASCADE;

-- A multifaceted look at organization annotation types over different
-- timescales

CREATE VIEW report.organization_annotation_types AS (
    SELECT
        timescale,
        MIN(start_date) AS start_date,
        MAX(end_date) AS end_date,
        period,
        organization_id,
        sub_type,
        shared,
        SUM(count) AS count
    FROM report.organization_annotation_counts
    GROUP BY period, timescale, sub_type, shared, organization_id
    ORDER BY period, timescale, sub_type, shared, organization_id
);
