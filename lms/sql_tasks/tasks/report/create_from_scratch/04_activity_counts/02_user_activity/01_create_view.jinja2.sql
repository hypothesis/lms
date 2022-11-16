DROP MATERIALIZED VIEW IF EXISTS report.user_activity CASCADE;

-- Annotation activity by users in a given period
CREATE MATERIALIZED VIEW report.user_activity AS (
    SELECT
        created_week,
        user_id,
        SUM(count) AS annotation_count
    FROM h.annotation_user_counts
    JOIN h.authorities ON
        annotation_user_counts.authority_id = authorities.id
        AND authorities.authority = '{{ region.authority }}'
        -- AND authorities.authority = 'lms.hypothes.is'
    GROUP BY created_week, user_id
    ORDER BY created_week, user_id
) WITH NO DATA;