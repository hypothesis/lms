DROP MATERIALIZED VIEW IF EXISTS report.groups CASCADE;

-- A view with our concept of a unique group in reporting, which happens to
-- mostly conform to an H group with extra metadata.

CREATE MATERIALIZED VIEW report.groups AS (
    WITH
        group_types AS (
            SELECT
                authority_provided_id,
                -- Every authority provided id should be unique to a type. But
                -- we sometimes get blank values (in _very_ few cases), but to
                -- be sure we should do a MAX here.
                MAX("type") AS type
            FROM (
                SELECT authority_provided_id, "type" FROM grouping
                UNION

                SELECT authority_provided_id, 'course' FROM course_groups_exported_from_h
                UNION

                SELECT
                    authority_provided_id,
                    CASE info->>'type'
                        -- Oh lordy, why...
                        WHEN 'course' THEN 'course'
                        WHEN 'course_group' THEN 'course'
                        WHEN 'blackboard_group_group' THEN 'blackboard_group'
                        WHEN 'canvas_group_group' THEN 'canvas_group'
                        WHEN 'section_group' THEN 'canvas_section'
                    END
                FROM group_info
            ) AS groups
            GROUP BY
                authority_provided_id
        )

    SELECT
        groups.id,
        groups.authority_provided_id,
        groups.name,
        group_types.type AS group_type,
        groups.created::date
    FROM h.group AS groups
    LEFT OUTER JOIN group_types ON
        groups.authority_provided_id = group_types.authority_provided_id
    WHERE
        groups.authority = '{{ region.authority }}'
        -- groups.authority = 'lms.hypothes.is'
    ORDER BY groups.created
) WITH NO DATA;
