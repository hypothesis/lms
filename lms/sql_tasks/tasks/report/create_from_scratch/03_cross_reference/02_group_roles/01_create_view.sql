DROP TYPE IF EXISTS report.roles CASCADE;

CREATE TYPE report.roles AS ENUM (
    'teacher', 'user'
);

DROP MATERIALIZED VIEW IF EXISTS report.group_roles CASCADE;

-- A table categorizing users as teachers and/or users in certain groups

CREATE MATERIALIZED VIEW report.group_roles AS (
    WITH
        teachers_from_group_info AS (
            SELECT
                groups.id as group_id,
                user_map.user_id
            FROM (
                SELECT
                    application_instance_id,
                    authority_provided_id,
                    jsonb_array_elements(info->'instructors') as instructor_info
                FROM group_info
            ) AS old_teachers_json
            JOIN report.groups ON
                groups.authority_provided_id = old_teachers_json.authority_provided_id
            JOIN "user" AS lms_user ON
                -- The user_id here is only unique in the AI
                lms_user.user_id = old_teachers_json.instructor_info->>'provider_unique_id'
                AND lms_user.application_instance_id = old_teachers_json.application_instance_id
            JOIN report.user_map ON
                lms_user.id = user_map.lms_user_id
        ),

        -- We might not be getting any additional info here that we don't get
        -- from group_info above, but this is more future proofed, as at some
        -- point we will want to remove group info.
        teachers_from_assignments AS (
            SELECT
                group_map.group_id,
                user_map.user_id
            FROM assignment_membership
            JOIN assignment_grouping ON
                assignment_membership.assignment_id = assignment_grouping.assignment_id
            JOIN report.group_map ON
                assignment_grouping.grouping_id = group_map.lms_grouping_id
            JOIN report.user_map ON
                assignment_membership.user_id = user_map.lms_user_id
            JOIN lti_role ON
                lti_role.id = lti_role_id
                AND lti_role.type = 'instructor'
        )

    SELECT * FROM (
        SELECT group_id, user_id, 'teacher'::report.roles AS role FROM teachers_from_group_info
        UNION
        SELECT group_id, user_id, 'teacher'::report.roles FROM teachers_from_assignments
        UNION
        -- We count anyone in a group as a "user". It's not clear that there
        -- could be a user who isn't allocated to a group apart from in error
        -- situations.
        SELECT group_id, user_id, 'user'::report.roles FROM report.user_groups
    ) AS data
    ORDER BY group_id, role, user_id
) WITH NO DATA;