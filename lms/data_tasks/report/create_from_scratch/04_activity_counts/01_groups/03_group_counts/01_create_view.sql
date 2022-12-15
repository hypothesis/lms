DROP MATERIALIZED VIEW IF EXISTS report.group_counts CASCADE;

-- Counts for groups which do not depend on time, one row per group.

CREATE MATERIALIZED VIEW report.group_counts AS (
    SELECT
        group_id,
        COUNT(DISTINCT(user_id)) FILTER (WHERE role = 'teacher') AS teacher_count,
        COUNT(DISTINCT(user_id)) FILTER (WHERE role = 'user') AS user_count
    FROM report.group_roles
    GROUP BY group_id
) WITH NO DATA;
