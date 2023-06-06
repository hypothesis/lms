DROP INDEX IF EXISTS report.organization_assignments_organization_id_assignment_id_idx;

REFRESH MATERIALIZED VIEW report.organization_assignments;

ANALYSE report.organization_assignments;

-- A unique index is mandatory for concurrent updates used in the refresh
CREATE UNIQUE INDEX organization_assignments_organization_id_assignment_id_idx ON report.organization_assignments (organization_id, assignment_id);
