DROP TYPE IF EXISTS report.academic_timescale CASCADE;

CREATE TYPE report.academic_timescale AS ENUM (
    'week', 'month', 'semester', 'academic_year', 'trailing_year', 'all_time'
);

DROP MATERIALIZED VIEW IF EXISTS report.organization_activity CASCADE;

-- A multifaceted look at organization activity over different timescales and
-- roles.

CREATE MATERIALIZED VIEW report.organization_activity AS (
    WITH
        -- In order to get all the combinations of different types of data we
        -- want in this table without writing an explosion of queries we first
        -- create a "facets" CTE which represents all the different
        -- combinations of values we want to be able to filter by.

        weeks AS (
            SELECT timestamp_week FROM report.events
            UNION
            SELECT created_week AS timestamp_week FROM report.group_activity
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
        ),

        -- Then we join onto this facets table and use it to group our data in
        -- all of the different combos.

        annotation_counts AS (
            SELECT
                facets.period,
                facets.timescale,
                facets.role,
                group_map.organization_id,
                SUM(count) AS annotation_count
            FROM facets
            JOIN report.group_annotation_counts ON
                group_annotation_counts.created_week = facets.timestamp_week
                AND group_annotation_counts.role = facets.role
            JOIN report.group_map ON
                group_annotation_counts.group_id = group_map.group_id
            GROUP BY
                facets.period, facets.timescale, facets.role, group_map.organization_id
        ),

        active AS (
            SELECT
                facets.period,
                facets.timescale,
                facets.role,
                events.organization_id,
                COUNT(DISTINCT(events.user_id)) AS active
            FROM facets
            JOIN report.events ON
                events.timestamp_week = facets.timestamp_week
            JOIN report.organization_roles ON
                organization_roles.organization_id = events.organization_id
                AND organization_roles.user_id = events.user_id
                AND organization_roles.role = facets.role
            WHERE
                event_type = 'configured_launch'
            GROUP BY
                facets.period, facets.timescale, facets.role, events.organization_id
        ),

        -- A billable user is defined as any user who is in a group which has
        -- at least one annotation in the period in question.
        billable AS (
            SELECT
                facets.period,
                facets.timescale,
                facets.role,
                group_map.organization_id,
                COUNT(DISTINCT(user_groups.user_id)) AS billable
            FROM facets
            JOIN report.group_activity ON
                group_activity.created_week = facets.timestamp_week
                AND group_activity.annotation_count > 0
            JOIN report.group_map ON
                group_activity.group_id = group_map.group_id
            JOIN report.user_groups ON
                user_groups.group_id = group_activity.group_id
            JOIN report.organization_roles ON
                organization_roles.organization_id = group_map.organization_id
                AND organization_roles.user_id = user_groups.user_id
                AND organization_roles.role = facets.role
            GROUP BY
                 facets.period, facets.timescale, facets.role, group_map.organization_id
        ),

        launch_count AS (
            SELECT
                period,
                timescale,
                organization_roles.role,
                events.organization_id,
                SUM(events.event_count) AS launch_count
            FROM report.events
            JOIN report.organization_roles ON
                events.user_id = organization_roles.user_id
                AND events.organization_id = organization_roles.organization_id
            JOIN facets ON
                events.timestamp_week = facets.timestamp_week
                AND organization_roles.role = facets.role
            WHERE event_type = 'configured_launch'
            GROUP BY
                period, timescale, organization_roles.role, events.organization_id
            ORDER BY
                period, timescale, organization_roles.role, events.organization_id
        ),

        -- We need to combine the data. A join seems the most natural way of
        -- doing it but causes trouble as we aren't guaranteed a row for each
        -- different type of data. To get around this we'll union all the rows
        -- together, spacing out the data so they end in different columns.

        unioned_metrics AS (
            SELECT
                period, timescale, organization_id, role,
                annotation_count, 0 AS active, 0 AS billable, 0 AS launch_count
            FROM annotation_counts

            UNION ALL

            SELECT
                period, timescale, organization_id, role,
                0, active, 0, 0
            FROM active

            UNION ALL

            SELECT
                period, timescale, organization_id, role,
                0, 0, billable, 0
            FROM billable

            UNION ALL

            SELECT
                period, timescale, organization_id, role,
                0, 0, 0, launch_count
            FROM launch_count
        )

    -- We can then finally MAX over the columns to get a single row with each
    -- value in it's own column.

    SELECT
        timescale,
        period::DATE AS start_date,
        (period + report.single_interval(timescale::text))::DATE AS end_date,
        report.present_date(timescale::text, period) AS period,
        role,
        organization_id,
        COALESCE(MAX(active), 0) AS active,
        COALESCE(MAX(billable), 0) AS billable,
        COALESCE(MAX(annotation_count), 0) AS annotation_count,
        COALESCE(MAX(launch_count), 0) AS launch_count
    FROM unioned_metrics
    WHERE organization_id IS NOT NULL
    GROUP BY period, timescale, role, organization_id
    ORDER BY period, timescale, role, organization_id
) WITH NO DATA;
