DROP MATERIALIZED VIEW IF EXISTS report.user_map CASCADE;

-- Map from LMS users to our internal concept of a unique reporting user
CREATE MATERIALIZED VIEW report.user_map AS (
    SELECT
        lms_users.id AS lms_user_id,
        raw_users.id AS user_id,
        application_instances.organization_id
    FROM "user" AS lms_users
    JOIN report.raw_users ON
        raw_users.username = SUBSTRING(SPLIT_PART(lms_users.h_userid, '@', 1), 6)
    JOIN application_instances ON
        lms_users.application_instance_id = application_instances.id
    ORDER BY lms_user_id, user_id
) WITH NO DATA;
