DROP INDEX IF EXISTS report.groups_id_idx;
DROP INDEX IF EXISTS report.groups_authority_provided_id_idx;
DROP INDEX IF EXISTS report.groups_group_type_idx;
DROP INDEX IF EXISTS report.groups_created_idx;

REFRESH MATERIALIZED VIEW report.groups;

ANALYSE report.groups;

-- A unique index is mandatory for concurrent updates used in the refresh
CREATE UNIQUE INDEX groups_id_idx ON report.groups (id);
CREATE INDEX groups_authority_provided_id_idx ON report.groups USING HASH (authority_provided_id);
CREATE INDEX groups_group_type_idx ON report.groups USING HASH (group_type);
CREATE INDEX groups_created_idx ON report.groups USING BRIN (created);
