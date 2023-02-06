DROP INDEX IF EXISTS report.organization_to_organization_parent_id_organization_id_idx;

REFRESH MATERIALIZED VIEW report.organization_to_organization;

ANALYSE report.organization_to_organization;

-- A unique index is mandatory for concurrent updates used in the refresh
CREATE UNIQUE INDEX organization_to_organization_parent_id_organization_id_idx ON report.organization_to_organization (parent_id, relation, child_id);
