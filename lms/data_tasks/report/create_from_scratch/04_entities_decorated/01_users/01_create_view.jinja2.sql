DROP MATERIALIZED VIEW IF EXISTS report.users CASCADE;

CREATE MATERIALIZED VIEW report.users AS (
    WITH
        user_modify_dates AS (
            -- Look for evidence of activity based on created and updated dates
            SELECT
                user_map.user_id,
                MIN(lms_user.created) AS first_active_date,
                MAX(lms_user.updated) AS last_active_date
            FROM report.user_map
            JOIN "user" AS lms_user ON
                lms_user.id = user_map.lms_user_id
            GROUP BY user_map.user_id
        ),

        user_activity_dates AS (
            SELECT
                user_id,
                MIN(active_date) AS first_active_date,
                MAX(active_date) AS last_active_date
            FROM (
                -- Using a weekly timestamp here loses us some accuracy, but
                -- it's way faster than going through the whole annotation table
                -- We'll use the H table directly to avoid dependency loops
                SELECT
                    user_id,
                    created_week AS active_date
                FROM h.annotation_counts
                JOIN h.authorities ON
                    annotation_counts.authority_id = authorities.id
                    AND authorities.authority = '{{ h_authority }}'

                UNION ALL

                -- Ideally we'd power this metric entirely with login info, but
                -- our data doesn't go back far enough. So we merge it with
                -- annotation information to give us a better idea
                SELECT
                    user_id,
                    timestamp_week AS active_date
                FROM report.events
                WHERE event_type IN ('deep_linking', 'configured_launch')
            ) AS data
            GROUP BY user_id
        ),

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
        -- Add a column which indicates that a user is a teacher in at least
        -- one context. This helps us notice / demonstrate we are only keeping
        -- teacher contact info. Keeping student contact info out of region is
        -- not permitted.
        CASE
            WHEN user_details.is_teacher IS true THEN true ELSE false
        END AS is_teacher,
        -- Daily resolution is fine. Some of these are only accurate to the week
        LEAST(
            raw_users.registered_date,
            user_modify_dates.first_active_date,
            user_activity_dates.first_active_date
        )::DATE AS first_active_date,
        GREATEST(
            user_activity_dates.last_active_date,
            user_modify_dates.last_active_date
        )::DATE AS last_active_date
    FROM report.raw_users
    LEFT OUTER JOIN user_details ON
        user_details.user_id = raw_users.id
    LEFT OUTER JOIN user_modify_dates ON
        user_modify_dates.user_id = raw_users.id
    LEFT OUTER JOIN user_activity_dates ON
        user_activity_dates.user_id = raw_users.id
) WITH NO DATA;
