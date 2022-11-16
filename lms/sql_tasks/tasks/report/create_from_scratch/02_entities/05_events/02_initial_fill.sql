DROP INDEX IF EXISTS report.events_timestamp_week_organization_id_event_type_user_id_idx;

REFRESH MATERIALIZED VIEW report.events;

ANALYSE report.events;

-- A unique index is mandatory for concurrent updates used in the refresh
CREATE UNIQUE INDEX events_timestamp_week_organization_id_event_type_user_id_idx ON report.events (timestamp_week, organization_id, event_type, user_id);