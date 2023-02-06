DROP MATERIALIZED VIEW IF EXISTS report.organization_to_organization CASCADE;

-- A view to simplify looking up all children, or all parents of a given group
CREATE MATERIALIZED VIEW report.organization_to_organization AS (
    SELECT
        parent_id,
        relation::report.tree_relation,
        child_id
    FROM (
        SELECT DISTINCT
            id AS parent_id,
            'self'::report.tree_relation AS relation,
            id AS child_id
        FROM organization

        UNION ALL

        SELECT DISTINCT
            parent_id AS parent_id,
            'parent'::report.tree_relation AS relation,
            id AS child_id
        FROM organization
        WHERE parent_id IS NOT NULL

        -- We aren't doing any recursive stuff here to add on the 'ancestor'
        -- indirect relationship because there aren't any yet, but when there
        -- are we can update this and everything based on it should work
    ) AS data
    ORDER BY parent_id, relation, child_id
) WITH NO DATA;
