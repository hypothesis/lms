DROP MATERIALIZED VIEW IF EXISTS report.group_annotation_counts CASCADE;

-- A weekly count of groups with annotation activity
CREATE MATERIALIZED VIEW report.group_annotation_counts AS (
    SELECT
        user_annotation_counts.group_id,
        user_annotation_counts.created_week,
        group_roles.role,
        user_annotation_counts.sub_type,
        user_annotation_counts.shared,
        SUM(user_annotation_counts.count) AS count
    FROM report.user_annotation_counts
    JOIN report.group_roles ON
        group_roles.group_id = user_annotation_counts.group_id
        AND group_roles.user_id = user_annotation_counts.user_id
    GROUP BY
        user_annotation_counts.group_id,
        user_annotation_counts.created_week,
        group_roles.role,
        user_annotation_counts.sub_type,
        user_annotation_counts.shared
    ORDER BY
        user_annotation_counts.group_id,
        user_annotation_counts.created_week,
        count DESC
) WITH NO DATA;
