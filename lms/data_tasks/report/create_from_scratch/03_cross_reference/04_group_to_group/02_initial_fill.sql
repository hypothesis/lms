DROP INDEX IF EXISTS report.group_to_group_parent_id_group_id_idx;

REFRESH MATERIALIZED VIEW report.group_to_group;

ANALYSE report.group_to_group;

-- A unique index is mandatory for concurrent updates used in the refresh
CREATE UNIQUE INDEX group_to_group_parent_id_group_id_idx ON report.group_to_group (parent_id, relation, child_id);
