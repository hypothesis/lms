DROP VIEW IF EXISTS report.group_bubbled_activity CASCADE;

-- A weekly count of groups with annotation activity, but with counts summed
-- up and down between parents and children as appropriate.

CREATE MATERIALIZED VIEW report.group_bubbled_activity AS (
    SELECT
        bubble_up.created_week,
        bubble_up.group_id,
        bubble_up.annotation_count,
        bubble_up.annotation_shared_count,
        bubble_up.annotation_replies_count,
        bubble_down.launch_count

    -- Numbers we want to move from child to parent
    FROM (
        SELECT
            created_week,
            group_to_group.parent_id AS group_id,
            SUM(annotation_count) as annotation_count,
            SUM(annotation_shared_count) as annotation_shared_count,
            SUM(annotation_replies_count) as annotation_replies_count
        FROM report.group_to_group
        -- The join on group to group without a relation includes self,
        -- so the child_id here is all children and ourselves
        JOIN report.group_activity ON
            group_activity.group_id = group_to_group.child_id
        GROUP BY created_week, group_to_group.parent_id
    ) as bubble_up

     -- Numbers we want to move from parent to child
    JOIN (
        SELECT
            created_week,
            group_to_group.child_id AS group_id,
            SUM(launch_count) as launch_count
        FROM report.group_to_group
        -- The join on group to group without a relation includes self,
        -- so the parent_id here is our parent and ourselves
        JOIN report.group_activity ON
            group_activity.group_id = group_to_group.parent_id
        GROUP BY created_week, group_to_group.child_id
    ) AS bubble_down ON
        bubble_up.created_week = bubble_down.created_week
        AND bubble_up.group_id = bubble_down.group_id

    ORDER BY bubble_up.created_week, bubble_up.group_id
) WITH NO DATA;
