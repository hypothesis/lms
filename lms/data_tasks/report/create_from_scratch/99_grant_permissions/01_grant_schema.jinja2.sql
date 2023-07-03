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

    GRANT SELECT ON report.assignments TO "{{fdw_user}}";
    GRANT SELECT ON report.events TO "{{fdw_user}}";
    GRANT SELECT ON report.groups TO "{{fdw_user}}";
    GRANT SELECT ON report.group_map TO "{{fdw_user}}";
    GRANT SELECT ON report.group_annotation_counts TO "{{fdw_user}}";
    GRANT SELECT ON report.group_bubbled_annotation_counts TO "{{fdw_user}}";
    GRANT SELECT ON report.group_bubbled_activity TO "{{fdw_user}}";
    GRANT SELECT ON report.group_bubbled_counts TO "{{fdw_user}}";
    GRANT SELECT ON report.group_roles TO "{{fdw_user}}";
    GRANT SELECT ON report.organization_activity TO "{{fdw_user}}";
    GRANT SELECT ON report.organization_annotation_counts TO "{{fdw_user}}";
    GRANT SELECT ON report.organization_annotation_types TO "{{fdw_user}}";
    GRANT SELECT ON report.organization_assignments TO "{{fdw_user}}";
    GRANT SELECT ON report.organization_roles TO "{{fdw_user}}";
    GRANT SELECT ON report.users TO "{{fdw_user}}";
    GRANT SELECT ON report.user_annotation_counts TO "{{fdw_user}}";
    GRANT SELECT ON report.users_sensitive TO "{{fdw_user}}";
{% endfor %}
