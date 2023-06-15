DROP MATERIALIZED VIEW IF EXISTS report.group_type_counts CASCADE;

-- A weekly count of group annotation types limited to the correct authority

CREATE MATERIALIZED VIEW report.group_type_counts AS (
    SELECT
        created_week,
        group_id,
        sub_type,
        shared,
        count
    FROM h.annotation_type_group_counts
    JOIN h.authorities ON
        annotation_type_group_counts.authority_id = authorities.id
        AND authorities.authority = '{{ region.authority }}'
) WITH NO DATA;
