DROP MATERIALIZED VIEW IF EXISTS report.users CASCADE;

-- I'm not sure this is completely required right now, but it makes things
-- simple to think about, as it represents our concept of a unique user in
-- the reporting space. That happens to basically be an H user at the moment,
-- but we are likely to tack on extra details in future, like email address
-- etc.

CREATE MATERIALIZED VIEW report.users AS 
  (SELECT id, 
          username, 
          registered_date::date 
   FROM h.user AS users 
   WHERE users.authority = '{{ region.authority }}' -- users.authority = 'lms.hypothes.is'

   ORDER BY registered_date) WITH NO DATA;