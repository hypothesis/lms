DROP VIEW IF EXISTS report.group_bubbled_activity CASCADE;

-- A weekly count of groups with annotation activity, but with counts summed
-- up and down between parents and children as appropriate.

CREATE MATERIALIZED VIEW report.group_bubbled_activity AS (
    SELECT
        created_week,
        group_to_group.parent_id AS group_id,
        SUM(annotation_count) AS annotation_count,
        SUM(annotation_shared_count) AS annotation_shared_count,
        SUM(annotation_replies_count) AS annotation_replies_count,
        SUM(launch_count) AS launch_count
    FROM report.group_to_group
    -- The join on group to group without a relation includes self,
    -- so the child_id here is all children and ourselves
    JOIN report.group_activity ON
        group_activity.group_id = group_to_group.child_id
    GROUP BY created_week, group_to_group.parent_id
    ORDER BY created_week, group_to_group.parent_id
) WITH NO DATA;
