DROP TYPE IF EXISTS report.academic_timescale CASCADE;

CREATE TYPE report.academic_timescale AS ENUM (
    'week', 'month', 'semester', 'academic_year', 'trailing_year', 'all_time'
);


DROP MATERIALIZED VIEW IF EXISTS report.organization_annotation_counts CASCADE;

-- A multifaceted look at organization annotation sub-types over different
-- timescales

CREATE MATERIALIZED VIEW report.organization_annotation_counts AS (
    WITH
        -- In order to get all the combinations of different types of data we
        -- want in this table without writing an explosion of queries we first
        -- create a "facets" CTE which represents all the different
        -- combinations of values we want to be able to filter by.

        -- We could probably do without this, but it makes it more like the
        -- `organization_activity` query
        weeks AS (
            SELECT DISTINCT(created_week) AS timestamp_week
            FROM report.group_annotation_counts
        ),

        timescales AS (
            SELECT column1 AS timescale FROM (
                VALUES
                    ('week'),
                    ('month'),
                    ('semester'),
                    ('academic_year'),
                    ('trailing_year'),
                    ('all_time')
            ) AS data
        ),

        roles AS (
            SELECT column1::report.roles AS role FROM (
                VALUES ('user'), ('teacher')
            ) AS data
        ),

        periods AS (
            SELECT
                timestamp_week,
                timescale::report.academic_timescale,
                report.multi_truncate(timescale, timestamp_week) AS period
            FROM weeks
            CROSS JOIN timescales
        ),

        facets AS (
            SELECT * FROM periods
            CROSS JOIN roles
        )

    SELECT
        timescale,
        period::DATE AS start_date,
        (period + report.single_interval(timescale::text))::DATE AS end_date,
        facets.role,
        report.present_date(timescale::text, period) AS period,
        group_map.organization_id,
        group_annotation_counts.sub_type,
        group_annotation_counts.shared,
        SUM(group_annotation_counts.count) AS count
    FROM facets
    JOIN report.group_annotation_counts ON
        group_annotation_counts.created_week = facets.timestamp_week
        AND group_annotation_counts.role = facets.role
    JOIN report.group_map ON
        group_map.group_id = group_annotation_counts.group_id
    GROUP BY period, timescale, facets.role, sub_type, shared, organization_id
    ORDER BY period, timescale, facets.role, sub_type, shared, organization_id
) WITH NO DATA;
