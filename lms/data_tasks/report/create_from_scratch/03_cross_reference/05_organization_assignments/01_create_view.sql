DROP MATERIALIZED VIEW IF EXISTS report.organization_assignments CASCADE;

-- A view which links assignments to organizations in a convenient way

CREATE MATERIALIZED VIEW report.organization_assignments AS (
    SELECT
        application_instances.organization_id,
        assignment_grouping.assignment_id
    FROM assignment_grouping
    JOIN grouping ON
        grouping.id = grouping_id
    JOIN application_instances ON
        application_instances.id = grouping.application_instance_id
    GROUP BY
        application_instances.organization_id,
        assignment_grouping.assignment_id
    ORDER BY
        application_instances.organization_id,
        assignment_grouping.assignment_id
) WITH NO DATA;
