DROP MATERIALIZED VIEW IF EXISTS report.group_bubbled_annotation_counts CASCADE;

-- A weekly count of groups with annotation activity, but with counts summed
-- up and down between parents and children as appropriate.

CREATE MATERIALIZED VIEW report.group_bubbled_annotation_counts AS (
    SELECT
        group_to_group.parent_id AS group_id,
        created_week,
        role,
        sub_type,
        shared,
        SUM(count) AS count
    FROM report.group_to_group
    -- The join on group to group without a relation includes self,
    -- so the child_id here is all children and ourselves
    JOIN report.group_annotation_counts ON
        group_annotation_counts.group_id = group_to_group.child_id
    GROUP BY group_to_group.parent_id, created_week, role, sub_type, shared
    ORDER BY group_to_group.parent_id, created_week, count DESC
) WITH NO DATA;
