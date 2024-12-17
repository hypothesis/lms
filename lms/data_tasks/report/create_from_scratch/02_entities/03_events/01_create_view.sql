DROP TYPE IF EXISTS report.event_type CASCADE;

CREATE TYPE report.event_type AS ENUM (
    'configured_launch',
    'deep_linking',
    'audit',
    'edited_assignment',
    'submission',
    'grade',
    'error_code'
);

DROP MATERIALIZED VIEW IF EXISTS report.events CASCADE;

-- A compressed version of the event table aggregated by week

CREATE MATERIALIZED VIEW report.events AS (
    WITH
        -- Unique event user relations without considering role
        unique_event_users AS (
            SELECT DISTINCT event_id, user_id FROM event_user
        ),

        translated_events AS (
            SELECT
                report.multi_truncate('week', timestamp::date) AS timestamp_week,
                user_map.organization_id,
                event_type.type::report.event_type AS event_type,
                user_map.user_id
            FROM event
            JOIN event_type ON
                event.type_id = event_type.id
            -- Lots of events don't have users
            LEFT OUTER JOIN unique_event_users ON
                unique_event_users.event_id = event.id
            LEFT OUTER JOIN report.user_map ON
                unique_event_users.user_id = user_map.lms_user_id
        )

    SELECT
        translated_events.*,
        COUNT(1) AS event_count
    FROM translated_events
    GROUP BY timestamp_week, organization_id, event_type, user_id
    ORDER BY timestamp_week, organization_id, event_type, user_id
) WITH NO DATA;


