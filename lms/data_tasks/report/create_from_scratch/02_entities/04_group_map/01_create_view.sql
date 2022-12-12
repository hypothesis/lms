DROP MATERIALIZED VIEW IF EXISTS report.group_map CASCADE;

-- Map LMS groupings and organizations to reporting groups

CREATE MATERIALIZED VIEW report.group_map AS (
    WITH
        all_groups AS (
            SELECT
                grouping.id AS lms_grouping_id,
                grouping.parent_id AS lms_grouping_parent_id,
                -- Coalesce the ids in case the left or right side is missing
                COALESCE(
                    grouping.authority_provided_id,
                    group_info.authority_provided_id
                ) AS authority_provided_id,
                COALESCE(
                    grouping.application_instance_id,
                    group_info.application_instance_id
                ) AS application_instance_id
            FROM grouping
            -- Do a full outer join here so a result from either side will
            -- result in a record
            FULL OUTER JOIN group_info ON
                group_info.authority_provided_id = grouping.authority_provided_id
                AND group_info.application_instance_id = grouping.application_instance_id
        ),

        group_map AS (
            SELECT
                lms_grouping_id,
                lms_grouping_parent_id,
                groups.id AS group_id,
                application_instances.organization_id
            FROM all_groups
            JOIN report.groups ON
                all_groups.authority_provided_id = groups.authority_provided_id
            JOIN application_instances ON
                all_groups.application_instance_id = application_instances.id
            ORDER BY lms_grouping_id, group_id
        )

    SELECT
        group_map.lms_grouping_id,
        group_map.lms_grouping_parent_id,
        group_map.group_id,
        parent_group_map.group_id AS group_parent_id,
        group_map.organization_id
    FROM group_map
    LEFT OUTER JOIN group_map AS parent_group_map ON
        parent_group_map.lms_grouping_id = group_map.lms_grouping_parent_id
        AND parent_group_map.lms_grouping_id is NOT NULL
    ORDER BY lms_grouping_id
) WITH NO DATA;
