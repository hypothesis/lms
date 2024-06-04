DROP MATERIALIZED VIEW IF EXISTS report.user_groups CASCADE;

-- A limited set of user groupings imported from H to speed up queries here

CREATE MATERIALIZED VIEW report.user_groups AS (
    SELECT
         user_id,
         group_id
    FROM h.user_group
    JOIN h.users ON
        users.id = user_group.user_id
        AND users.authority = '{{ h_authority }}'
    ORDER BY registered_date
) WITH NO DATA;
