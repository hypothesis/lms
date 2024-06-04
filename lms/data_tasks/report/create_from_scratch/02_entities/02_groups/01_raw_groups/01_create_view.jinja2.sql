DROP VIEW IF EXISTS report.raw_groups CASCADE;

-- A view with our concept of a unique group in reporting, which happens to
-- mostly conform to an H group with extra metadata. This view is not to be
-- used directly, but is consumed by `report.groups`.

-- About `authority_provided_ids`
-- ==============================
-- The authority provided id is based on a number of things:
--
--   * The GUID
--   * The unique id provided by the LMS for the grouping
--   * Our type (course, section etc.)
--
-- It is *not* based on the application instance id at all.

CREATE VIEW report.raw_groups AS (
    WITH
        group_types AS (
            SELECT
                authority_provided_id,
                -- Every authority provided id should be unique to a type. But
                -- we sometimes get blank values (in _very_ few cases), but to
                -- be sure we should do a MAX here.
                MAX("type") AS type,
                MAX(lms_name) AS name
            FROM (
                SELECT authority_provided_id, "type", lms_name FROM grouping
                UNION

                SELECT authority_provided_id, 'course', NULL FROM course_groups_exported_from_h
                UNION

                SELECT
                    authority_provided_id,
                    CASE info->>'type'
                        -- Oh lordy, why...
                        WHEN 'course' THEN 'course'
                        WHEN 'course_group' THEN 'course'
                        WHEN 'blackboard_group_group' THEN 'blackboard_group'
                        WHEN 'canvas_group_group' THEN 'canvas_group'
                        WHEN 'd2l_group_group' THEN 'canvas_group'
                        WHEN 'section_group' THEN 'canvas_section'
                    END,
                    context_title
                FROM group_info
            ) AS groups
            GROUP BY authority_provided_id
        )

    SELECT
        groups.id,
        groups.authority_provided_id,
        CASE
            WHEN group_types.name IS NOT NULL THEN group_types.name
            ELSE groups.name
        END as name,
        group_types.type AS group_type,
        groups.created::date
    FROM h.groups
    LEFT OUTER JOIN group_types ON
        groups.authority_provided_id = group_types.authority_provided_id
    WHERE
        groups.authority = '{{ h_authority }}'
    ORDER BY groups.created
);
