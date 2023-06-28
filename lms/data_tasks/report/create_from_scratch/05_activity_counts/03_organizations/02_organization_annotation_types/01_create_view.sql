DROP MATERIALIZED VIEW IF EXISTS report.organization_annotation_types CASCADE;

-- A multifaceted look at organization annotation types over different
-- timescales

CREATE MATERIALIZED VIEW report.organization_annotation_types AS (
    WITH
        -- In order to get all the combinations of different types of data we
        -- want in this table without writing an explosion of queries we first
        -- create a "facets" CTE which represents all the different
        -- combinations of values we want to be able to filter by.

        -- We could probably do without this, but it makes it more like the
        -- `organization_activity` query
        weeks AS (
            SELECT DISTINCT(created_week) AS timestamp_week
            FROM report.group_type_counts
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

        facets AS (
            SELECT
                timestamp_week,
                timescale::report.academic_timescale,
                report.multi_truncate(timescale, timestamp_week) AS period
            FROM weeks
            CROSS JOIN timescales
        )

    SELECT
        timescale,
        period::DATE AS start_date,
        (period + report.single_interval(timescale::text))::DATE AS end_date,
        report.present_date(timescale::text, period) AS period,
        group_map.organization_id,
        group_type_counts.sub_type,
        group_type_counts.shared,
        SUM(group_type_counts.count) AS count
    FROM facets
    JOIN report.group_type_counts ON
        group_type_counts.created_week = facets.timestamp_week
    JOIN report.group_map ON
        group_map.group_id = group_type_counts.group_id
    GROUP BY period, timescale, sub_type, shared, organization_id
    ORDER BY period, timescale, sub_type, shared, organization_id
) WITH NO DATA;
