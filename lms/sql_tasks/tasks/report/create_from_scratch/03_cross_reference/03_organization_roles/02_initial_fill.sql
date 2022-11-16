DROP INDEX IF EXISTS report.organization_roles_role_organization_id_user_id_role_idx;

REFRESH MATERIALIZED VIEW report.organization_roles;

ANALYSE report.organization_roles;

-- A unique index is mandatory for concurrent updates used in the refresh

CREATE UNIQUE INDEX organization_roles_organization_id_role_user_id_role_idx ON report.organization_roles (organization_id, role, user_id);