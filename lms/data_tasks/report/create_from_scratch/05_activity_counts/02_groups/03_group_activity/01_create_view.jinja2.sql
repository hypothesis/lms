DROP MATERIALIZED VIEW IF EXISTS report.group_activity CASCADE;

-- A weekly count of groups with annotation activity

CREATE MATERIALIZED VIEW report.group_activity AS (
    WITH
        launch_counts AS (
            SELECT
                report.multi_truncate('week', timestamp) AS timestamp_week,
                group_id,
                COUNT(1) AS launch_count
            FROM report.group_map
            -- Our rolled up events counts table is rolled by by org and user
            -- which means we can't easily re-use if for groups. Not sure
            -- that's avoidable really. It can't be rolled up with everything
            -- without becoming the event table again. Regardless this is slow
            JOIN event ON
                event.course_id = group_map.lms_grouping_id
                OR event.grouping_id = group_map.lms_grouping_id
            JOIN event_type ON
                event_type.id = event.type_id
                AND event_type.type = 'configured_launch'
            GROUP BY timestamp_week, group_id
        ),

        annotation_counts AS (
            SELECT
                created_week,
                group_id,
                SUM(count) AS annotation_count,
                SUM(count) FILTER (WHERE shared=True) AS annotation_shared_count,
                SUM(count) FILTER (WHERE sub_type='reply') AS annotation_replies_count
            FROM h.annotation_counts
            JOIN h.authorities ON
                annotation_counts.authority_id = authorities.id
                AND authorities.authority = '{{ h_authority }}'
            GROUP BY created_week, group_id
        )

    SELECT
        COALESCE(annotation_counts.created_week, launch_counts.timestamp_week) AS created_week,
        COALESCE(annotation_counts.group_id, launch_counts.group_id) AS group_id,
        COALESCE(annotation_counts.annotation_count, 0) AS annotation_count,
        COALESCE(annotation_counts.annotation_shared_count, 0) AS annotation_shared_count,
        COALESCE(annotation_counts.annotation_replies_count, 0) AS annotation_replies_count,
        COALESCE(launch_counts.launch_count, 0) AS launch_count
    FROM annotation_counts
    -- Do a full outer join to ensure we get counts for launches, even if there
    -- are no activity reports. Which is quite common for courses.
    FULL OUTER JOIN launch_counts ON
        launch_counts.group_id = annotation_counts.group_id
        AND launch_counts.timestamp_week = annotation_counts.created_week
) WITH NO DATA;
