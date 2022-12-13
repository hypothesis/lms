DROP MATERIALIZED VIEW IF EXISTS report.groups CASCADE;

-- A view with our concept of a unique group in reporting, which happens to
-- mostly conform to an H group with extra metadata. This differs from the
-- `report.raw_group` it is based on by adding `parent_id` information.

CREATE MATERIALIZED VIEW report.groups AS (
    SELECT
        raw_groups.id,
        parent_ids.parent_id,
        raw_groups.authority_provided_id,
        raw_groups.name,
        raw_groups.group_type,
        raw_groups.created
    FROM report.raw_groups

    -- Here we do a join across a lot of things to generate the parent group id
    -- if there is one, from the grouping table parent id
    LEFT OUTER JOIN (
        -- We might have multiple copies of the heirarchy in the grouping table
        -- from the perspective of different application instances. They should
        -- all line up, but just in case they don't we group by group id and
        -- pick the minimum `parent_id`
        SELECT
            raw_groups.id AS group_id,
            MIN(parent_group_map.group_id) AS parent_id
        FROM report.raw_groups
        JOIN report.group_map ON
            group_map.group_id = raw_groups.id
        JOIN grouping ON
            grouping.id = group_map.lms_grouping_id
            AND grouping.parent_id IS NOT NULL
        JOIN report.group_map AS parent_group_map
            ON parent_group_map.lms_grouping_id = grouping.parent_id
        GROUP BY raw_groups.id
    ) AS parent_ids ON
        raw_groups.id = parent_ids.group_id
    ORDER BY created
) WITH NO DATA;
