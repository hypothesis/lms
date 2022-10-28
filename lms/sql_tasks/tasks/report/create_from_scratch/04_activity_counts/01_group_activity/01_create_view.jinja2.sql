DROP MATERIALIZED VIEW IF EXISTS report.group_activity CASCADE;

-- A weekly count of groups with annotation activity

CREATE MATERIALIZED VIEW report.group_activity AS (
    SELECT
        created_week,
        group_id,
        count AS annotation_count
    FROM h.annotation_group_counts
    JOIN h.authorities ON
        annotation_group_counts.authority_id = authorities.id
        AND authorities.authority = '{{ region.authority }}'
        -- AND authorities.authority = 'lms.hypothes.is'
) WITH NO DATA;
