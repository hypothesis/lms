-- The public schema already exists but we need to grant usage to the user we
-- will map via FDW.

{% for fdw_user in fdw_users %}
    -- Permissions exist independently of the schema, so dropping the schema
    -- does not revoke permissions. We need to remove the existing permissions
    -- otherwise removing something the list below does not remove the
    -- permission.
    REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM "{{fdw_user}}";

    GRANT USAGE ON SCHEMA public TO "{{fdw_user}}";

    GRANT SELECT ON public.organization TO "{{fdw_user}}";
{% endfor %}

{% for fdw_user in fdw_users %}
    REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA report FROM "{{fdw_user}}";

    GRANT USAGE ON SCHEMA report TO "{{fdw_user}}";

    GRANT SELECT ON report.organization_activity TO "{{fdw_user}}";
{% endfor %}
