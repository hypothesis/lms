The JSTOR data is an example based on data provided to us by JSTOR.

The application instance information is gathered by running the following query
in Metabase and downloading the JSON:

```sql
    SELECT 
        id AS application_instance_id,
        custom_canvas_api_domain,
        tool_consumer_instance_name,
        SPLIT_PART(tool_consumer_instance_contact_email, '@', 2) AS contact_domain,
        SPLIT_PART(requesters_email, '@', 2) AS email_domain,
        lms_url
    FROM application_instances
    UNION
    SELECT
        application_instance_id,
        custom_canvas_api_domain,
        tool_consumer_instance_name,
        SPLIT_PART(tool_consumer_instance_contact_email, '@', 2) AS contact_domain,
        NULL,
        NULL
    FROM group_info
    ORDER BY application_instance_id DESC
```