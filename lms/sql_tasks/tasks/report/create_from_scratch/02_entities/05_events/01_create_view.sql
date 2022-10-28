DROP TYPE IF EXISTS report.event_type CASCADE;

CREATE TYPE report.event_type AS ENUM (
    'configured_launch', 'deep_linking'
);

DROP MATERIALIZED VIEW IF EXISTS report.events CASCADE;

-- A compressed version of the event table aggregated by week

CREATE MATERIALIZED VIEW report.events AS (
    WITH
        translated_events AS (
            SELECT
                DATE_TRUNC('week', timestamp)::date AS timestamp_week,
                user_map.organization_id,
                event_type.type::report.event_type AS event_type,
                user_map.user_id
            FROM event
            JOIN event_user ON
                event_user.event_id = event.id
            JOIN event_type ON
                event.type_id = event_type.id
            JOIN report.user_map ON
                event_user.user_id = user_map.lms_user_id
            GROUP BY
                timestamp, event_id, event_type.type, user_map.user_id, user_map.organization_id
        )

    SELECT
        timestamp_week,
        organization_id,
        event_type,
        user_id,
        COUNT(1) AS event_count
    FROM translated_events
    GROUP BY
        timestamp_week, organization_id, event_type, user_id
    ORDER BY timestamp_week, organization_id, event_type, user_id
) WITH NO DATA;


