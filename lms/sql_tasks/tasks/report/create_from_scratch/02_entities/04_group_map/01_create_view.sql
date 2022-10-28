DROP MATERIALIZED VIEW IF EXISTS report.group_map CASCADE;

-- Map LMS groupings to reporting groups

CREATE MATERIALIZED VIEW report.group_map AS (
    SELECT
        grouping.id AS lms_grouping_id,
        groups.id AS group_id,
        application_instances.organization_id
    FROM grouping
    JOIN report.groups ON
        grouping.authority_provided_id = groups.authority_provided_id
    JOIN application_instances ON
        grouping.application_instance_id = application_instances.id
    ORDER BY lms_grouping_id, group_id
) WITH NO DATA;
