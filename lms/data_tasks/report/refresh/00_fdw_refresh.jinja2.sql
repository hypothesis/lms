ALTER SERVER "h_server" OPTIONS(
    SET host '{{h_fdw.host}}', -- SECRET
    SET port '{{h_fdw.port}}', 
    SET dbname '{{h_fdw.dbname}}'
);


ALTER USER MAPPING FOR "{{db_user}}" SERVER "h_server" OPTIONS(
    SET user '{{h_fdw.user}}',
    SET password '{{h_fdw.password}}' -- SECRET
);
