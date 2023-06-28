DROP VIEW IF EXISTS report.users_sensitive CASCADE;

-- Create a plain view to act as a shim while we replace `users_sensitive`
CREATE VIEW report.users_sensitive AS (
    SELECT
        id, email, display_name
    FROM report.users
);
