DROP MATERIALIZED VIEW IF EXISTS user_contact_details CASCADE;

-- NOTE: This is SENSITIVE data! Do not keep this at rest outside of the region
-- it was created. A view is ok, a materialized view is not.

-- Contact details for users. At the moment this is limited to teachers only.
CREATE MATERIALIZED VIEW user_contact_details AS (
    WITH
        teachers_from_group_info AS (
            SELECT DISTINCT
                user_map.user_id,
                instructor_info->>'email' AS email,
                instructor_info->>'display_name' AS name
            FROM (
                SELECT
                    application_instance_id,
                    authority_provided_id,
                    jsonb_array_elements(info->'instructors') AS instructor_info
                FROM group_info
            ) AS old_teachers_json
            JOIN "user" AS lms_user ON
                -- The user_id here is only unique in the AI
                lms_user.user_id = old_teachers_json.instructor_info->>'provider_unique_id'
                AND lms_user.application_instance_id = old_teachers_json.application_instance_id
            JOIN report.user_map ON
                lms_user.id = user_map.lms_user_id
        ),

        -- Break (name, email) pairs into ("name", name) and ("email", email)
        -- rows to allow us to independently dedupe each type of data.
        uniques AS (
            SELECT
                DISTINCT
                user_id, type, value
            FROM teachers_from_group_info
            CROSS JOIN LATERAL (
                VALUES
                    ('email', teachers_from_group_info.email),
                    ('name', teachers_from_group_info.name)
            ) AS data (type, value)
            WHERE
                value IS NOT NULL
                AND value != ''
            ORDER BY user_id, type, value
        )

    SELECT
        user_id,
        type,
        -- Add an ordinal row (1 for the first email, 1 for the first name) so
        -- we can easily retrieve a single row for a user if we want. As a
        -- rough heuristic, we'll assume longer is more complete and therefore
        -- prioritise it first
        COUNT(1) OVER (PARTITION BY (user_id, type) ORDER BY LENGTH(value) DESC) AS ordinal,
        value
    FROM uniques
) WITH NO DATA;
