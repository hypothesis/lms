DROP INDEX IF EXISTS report.organization_activity_timescale_period_role_organization_id_idx;

REFRESH MATERIALIZED VIEW report.organization_activity;

ANALYSE report.organization_activity;

-- A unique index is mandatory for concurrent updates used in the refresh
CREATE UNIQUE INDEX organization_activity_timescale_period_role_organization_id_idx ON report.organization_activity (timescale, period, role, organization_id);
