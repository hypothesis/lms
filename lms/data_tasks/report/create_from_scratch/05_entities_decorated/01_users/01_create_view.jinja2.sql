DROP MATERIALIZED VIEW IF EXISTS report.users CASCADE;

CREATE MATERIALIZED VIEW report.users AS (
    WITH
        user_details AS (
            SELECT DISTINCT
                user_map.user_id,

                -- The order here should ensure empty strings and nulls are
                -- sorted to the back, so the "first" value should be non-null
                -- if possible
                FIRST_VALUE(lms_user.display_name) OVER (
                    PARTITION BY user_map.user_id
                    ORDER BY lms_user.display_name
                    RANGE BETWEEN
                        UNBOUNDED PRECEDING AND
                        UNBOUNDED FOLLOWING
                ) AS display_name,

                FIRST_VALUE(lms_user.email) OVER (
                    PARTITION BY user_map.user_id
                    ORDER BY lms_user.email
                    RANGE BETWEEN
                        UNBOUNDED PRECEDING AND
                        UNBOUNDED FOLLOWING
                ) AS email,

                true AS is_teacher
            FROM report.user_map
            JOIN "user" AS lms_user ON
                lms_user.id = user_map.lms_user_id
            WHERE
                -- Ensure we are only providing contact details for users who
                -- are a teacher in at least one context
                user_map.user_id IN (
                    SELECT DISTINCT(user_id)
                    FROM report.organization_roles
                    WHERE role = 'teacher'
                )
        )

    SELECT
        raw_users.id,
        user_details.display_name,
        user_details.email,
        raw_users.username,
        CASE
            WHEN user_details.is_teacher IS true THEN true ELSE false
        END AS is_teacher,
        -- Add a column which indicates that a user is a teacher in at least
        -- one context. This helps us notice / demonstrate we are only keeping
        -- teacher contact info. Keeping student contact info out of region is
        -- not permitted.
        raw_users.registered_date
    FROM report.raw_users
    LEFT OUTER JOIN user_details ON
        user_details.user_id = raw_users.id
) WITH NO DATA;
