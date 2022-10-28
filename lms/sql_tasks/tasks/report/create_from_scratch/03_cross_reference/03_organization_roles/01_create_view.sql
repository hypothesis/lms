DROP MATERIALIZED VIEW IF EXISTS report.organization_roles CASCADE;

-- A view which categorizes users as teachers and/or users in a given org

CREATE MATERIALIZED VIEW report.organization_roles AS (
    SELECT
        group_map.organization_id,
        group_roles.role,
        group_roles.user_id
    FROM report.group_roles
    JOIN report.group_map ON
        group_map.group_id = group_roles.group_id
    GROUP BY group_map.organization_id, group_roles.role, group_roles.user_id
) WITH NO DATA;
