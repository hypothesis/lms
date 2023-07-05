DROP VIEW IF EXISTS report.organizations CASCADE;

-- Create a proxy view to isolate LMS from reading our data directly
CREATE VIEW report.organizations AS (
    SELECT
        id,
        public_id,
        name,
        created,
        updated,
        enabled
    FROM organization
);
