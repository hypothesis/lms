DROP MATERIALIZED VIEW IF EXISTS report.assignments CASCADE;

-- A slightly sanitized copy of our assignments

CREATE MATERIALIZED VIEW report.assignments AS (
    WITH
        assignments AS (
            SELECT
                id,
                created,
                updated,
                -- Do some basic normalization
                TRIM(REPLACE(LOWER(document_url), '%3a%2f%2f', '://')) AS url
            FROM assignment
        )

    SELECT
        *,
        CASE
            -- Content integrations
            WHEN STARTS_WITH(url, 'blackboard://') THEN 'Blackboard Files'
            WHEN STARTS_WITH(url, 'moodle://file') THEN 'Moodle Files'
            WHEN STARTS_WITH(url, 'moodle://page') THEN 'Moodle Pages'
            WHEN STARTS_WITH(url, 'd2l://') THEN 'D2L Files'
            WHEN STARTS_WITH(url, 'canvas://file') THEN 'Canvas Files'
            WHEN STARTS_WITH(url, 'canvas://page') THEN 'Canvas Pages'
            WHEN STARTS_WITH(url, 'canvas-studio://') THEN 'Canvas Studio'
            WHEN STARTS_WITH(url, 'vitalsource://') THEN 'VitalSource'
            WHEN STARTS_WITH(url, 'jstor://') THEN 'JSTOR'
            WHEN STARTS_WITH(url, 'https://drive.google.com') THEN 'Google Drive'
            WHEN STARTS_WITH(url, 'https://api.onedrive.com') THEN 'Microsoft OneDrive'

            WHEN STARTS_WITH(url, 'https://www.youtube.com') THEN 'YouTube'
            WHEN STARTS_WITH(url, 'https://youtube.com') THEN 'YouTube'
            WHEN STARTS_WITH(url, 'https://youtu.be') THEN 'YouTube'

            -- We're assuming we've caught everything by here, but anything we
            -- miss will be in this pot. This should be Via stuff hopefully.
            WHEN STARTS_WITH(url, 'http:/') THEN 'PDF / HTML'
            WHEN STARTS_WITH(url, 'https:/') THEN 'PDF / HTML'

            -- A catch all term for all the weird detritus we end up with
            ELSE 'Other'
        END AS file_type
    FROM assignments
) WITH NO DATA;
