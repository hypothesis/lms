{% macro refresh_fdw_server(server_name, credentials, users) %}
    ALTER SERVER "{{server_name}}" OPTIONS(
        SET host '{{credentials.host}}', -- SECRET
        SET port '{{credentials.port}}', 
        SET dbname '{{credentials.dbname}}'
    );


    {% for user in users %}
        ALTER USER MAPPING FOR "{{user}}" SERVER "{{server_name}}" OPTIONS(
            SET user '{{credentials.user}}',
            SET password '{{credentials.password}}' -- SECRET
        );
    {% endfor %}
{% endmacro %}

{{ refresh_fdw_server("h_server", h_fdw, users=[db_user]) }}
