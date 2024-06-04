DROP MATERIALIZED VIEW IF EXISTS report.raw_users CASCADE;

-- The building blocks of a user. We won't export this. See
-- `*_entities_decorated/*_users` for the version for external consumers.
CREATE MATERIALIZED VIEW report.raw_users AS (
    SELECT
         id,
         username,
         registered_date::date
    FROM h.users
    WHERE
        users.authority = '{{ h_authority }}'
    ORDER BY registered_date
) WITH NO DATA;
