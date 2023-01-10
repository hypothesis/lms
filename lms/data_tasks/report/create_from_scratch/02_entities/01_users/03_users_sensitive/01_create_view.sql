DROP MATERIALIZED VIEW IF EXISTS report.users_sensitive CASCADE;

-- Create a separate table for sensitive user information, which should not be
-- stored out of region.
CREATE MATERIALIZED VIEW report.users_sensitive AS (
    SELECT DISTINCT
        user_map.user_id AS id,

        -- The order here should ensure empty strings and nulls are sorted to
        -- the back, so the "first" value should be non-null if possible
        FIRST_VALUE(users.email) OVER (
            PARTITION BY user_map.user_id
            ORDER BY users.email
            RANGE BETWEEN
                UNBOUNDED PRECEDING AND
                UNBOUNDED FOLLOWING
        ) AS email,

        FIRST_VALUE(users.display_name) OVER (
            PARTITION BY user_map.user_id
            ORDER BY users.display_name
            RANGE BETWEEN
                UNBOUNDED PRECEDING AND
                UNBOUNDED FOLLOWING
        ) AS display_name
    FROM report.user_map
    JOIN "user" AS users ON
        users.id = user_map.lms_user_id
    ORDER BY user_map.user_id
);
