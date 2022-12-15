DROP MATERIALIZED VIEW IF EXISTS report.group_counts CASCADE;

-- Counts for groups which do not depend on time, one row per group.

CREATE MATERIALIZED VIEW report.group_counts AS (
    WITH
        user_counts AS (
            SELECT
                group_id,
                COUNT(DISTINCT(user_id)) FILTER (WHERE role = 'teacher') AS teacher_count,
                COUNT(DISTINCT(user_id)) FILTER (WHERE role = 'user') AS user_count
            FROM report.group_roles
            GROUP BY group_id
        ),

        assignment_counts AS (
            SELECT
                group_map.group_id,
                COUNT(DISTINCT(assignment_grouping.assignment_id)) AS assignment_count,
                COUNT(DISTINCT(assignment.document_url)) AS document_count
            FROM assignment_grouping
            JOIN report.group_map ON
                group_map.lms_grouping_id = assignment_grouping.grouping_id
            JOIN assignment ON
                assignment.id = assignment_grouping.assignment_id
            GROUP BY group_map.group_id
        )

    SELECT
        user_counts.group_id,
        COALESCE(teacher_count, 0) AS teacher_count,
        COALESCE(user_count, 0) AS user_count,
        COALESCE(assignment_count, 0) AS assignment_count,
        COALESCE(document_count, 0) AS document_count
    FROM user_counts
    FULL OUTER JOIN assignment_counts ON
        user_counts.group_id = assignment_counts.group_id

) WITH NO DATA;
