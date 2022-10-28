DROP INDEX IF EXISTS report.users_user_id_group_id_idx;

REFRESH MATERIALIZED VIEW report.user_groups;

ANALYSE report.user_groups;

-- A unique index is mandatory for concurrent updates used in the refresh
CREATE UNIQUE INDEX users_user_id_group_id_idx ON report.user_groups (user_id, group_id);
