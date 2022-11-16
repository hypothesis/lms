DROP INDEX IF EXISTS report.group_roles_group_id_role_user_id_role_idx;

REFRESH MATERIALIZED VIEW report.group_roles;

ANALYSE report.group_roles;

-- A unique index is mandatory for concurrent updates used in the refresh

CREATE UNIQUE INDEX group_roles_group_id_role_user_id_role_idx ON report.group_roles (group_id, role, user_id);