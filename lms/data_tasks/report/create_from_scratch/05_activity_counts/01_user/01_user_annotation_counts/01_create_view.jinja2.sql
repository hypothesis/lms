DROP MATERIALIZED VIEW IF EXISTS report.user_annotation_counts CASCADE;

-- Annotations split by most different facets including user and group
CREATE MATERIALIZED VIEW report.user_annotation_counts AS (
    SELECT
        user_id,
        group_id,
        created_week,
        sub_type,
        shared,
        count
    FROM h.annotation_counts
    JOIN h.authorities ON
        annotation_counts.authority_id = authorities.id
        AND authorities.authority = '{{ h_authority }}'
    ORDER BY created_week, user_id, group_id, count DESC
) WITH NO DATA;
