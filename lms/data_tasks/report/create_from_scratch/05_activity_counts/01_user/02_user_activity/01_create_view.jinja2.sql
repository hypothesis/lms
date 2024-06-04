DROP MATERIALIZED VIEW IF EXISTS report.user_activity CASCADE;

-- Annotation activity by users in a given period
CREATE MATERIALIZED VIEW report.user_activity AS (
    SELECT
        created_week,
        user_id,
        SUM(count) AS annotation_count
    FROM h.annotation_counts
    JOIN h.authorities ON
        annotation_counts.authority_id = authorities.id
        AND authorities.authority = '{{ h_authority }}'
    GROUP BY created_week, user_id
    ORDER BY created_week, user_id
) WITH NO DATA;
