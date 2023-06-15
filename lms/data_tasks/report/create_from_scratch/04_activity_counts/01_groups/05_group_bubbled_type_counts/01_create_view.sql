DROP VIEW IF EXISTS report.group_bubbled_type_counts CASCADE;

-- A weekly count of annotation type, but with counts summed
-- up and down between parents and children as appropriate.

CREATE MATERIALIZED VIEW report.group_bubbled_type_counts AS (
    SELECT
        created_week,
        group_to_group.parent_id AS group_id,
        sub_type,
        shared,
        SUM(count) AS count
    FROM report.group_to_group
    -- The join on group to group without a relation includes self,
    -- so the child_id here is all children and ourselves
    JOIN report.group_type_counts ON
        group_type_counts.group_id = group_to_group.child_id
    GROUP BY created_week, group_to_group.parent_id, sub_type, shared
    ORDER BY created_week, group_to_group.parent_id, sub_type, shared
) WITH NO DATA;
