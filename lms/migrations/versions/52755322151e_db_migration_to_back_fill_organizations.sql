WITH
    -- A mapping of manual overrides for GUIDS for certain application instances
    guid_overrides AS (
        SELECT column1 AS application_instance_id, column2 AS guid FROM (
            VALUES
            -- The exact GUIDs here are taken from Sparky and are irrelevant
            -- so long as they are unique. This will ensure these ai's are
            -- treated separately.
            (529, '15a5afec178c4591914762c8019d6275_Metropolitan_State_College_of_Denver'),
            (1684, '15a5afec178c4591914762c8019d6275_Montgomery_College'),
            (3758, '375fd6b5351f43a69d06efa6952583f5_mccc2.blackboard.com'),
            (845, '375fd6b5351f43a69d06efa6952583f5_desales.blackboard.com'),
            (4301, '375fd6b5351f43a69d06efa6952583f5_learn.humber.ca'),
            (4744, 'Bv4oabGc5JWXEVx21igFQ0ldABpNNCl2ZpEAlGga:canvas-lms_uwlac.instructure.com'),
            (3859, 'Bv4oabGc5JWXEVx21igFQ0ldABpNNCl2ZpEAlGga:canvas-lms_uweau.instructure.com'),
            (3396, 'Bv4oabGc5JWXEVx21igFQ0ldABpNNCl2ZpEAlGga:canvas-lms_uwmil.instructure.com')
        ) as guid_overrides
    ),

    ids_and_guids AS (
        SELECT application_instance_id, guid FROM (
            -- Get all application instances and guids from group info
            SELECT
                group_info.application_instance_id,
                group_info.tool_consumer_instance_guid AS guid
            FROM group_info
            LEFT JOIN (SELECT * FROM guid_overrides) as overrides
                ON overrides.application_instance_id = group_info.application_instance_id
            WHERE
                tool_consumer_instance_guid != ''
                AND tool_consumer_instance_guid IS NOT NULL
                -- LEFT ANTI JOIN to filter out the `guid_overrides`
                AND overrides.application_instance_id is NULL

            UNION

            SELECT
                application_instances.id AS application_instance_id,
                application_instances.tool_consumer_instance_guid AS guid
            FROM application_instances
            LEFT JOIN (SELECT * FROM guid_overrides) as overrides
                ON overrides.application_instance_id = application_instances.id
            WHERE
                tool_consumer_instance_guid != ''
                AND tool_consumer_instance_guid IS NOT NULL
                  -- LEFT ANTI JOIN to filter out the `guid_overrides`
                AND overrides.application_instance_id is NULL

            UNION

            SELECT * FROM guid_overrides

        ) AS data
        GROUP BY application_instance_id, guid
    )

SELECT
    ids_and_guids_left.application_instance_id AS left_id,
    ids_and_guids_right.application_instance_id AS right_id
FROM ids_and_guids AS ids_and_guids_left
JOIN ids_and_guids AS ids_and_guids_right
    ON ids_and_guids_left.application_instance_id = ids_and_guids_right.application_instance_id
GROUP BY left_id, right_id