def includeme(config):  # pylint:disable=too-many-statements
    config.add_route("index", "/")
    config.add_route("feature_flags_test", "/flags/test")
    config.add_route("welcome", "/welcome")
    config.add_route("assets", "/assets/*subpath")
    config.add_route("status", "/_status")
    config.add_route("favicon", "/favicon.ico")
    config.add_route("ui-playground", "/ui-playground/*remainder")

    config.add_route("canvas.v11.config", "/config_xml")
    config.add_route("canvas.v13.config", "/canvas/1.3/config")
    config.add_route(
        "configure_assignment",
        "/assignment",
        request_method="POST",
        factory="lms.resources.LTILaunchResource",
    )
    config.add_route(
        "lti_launches", "/lti_launches", factory="lms.resources.LTILaunchResource"
    )
    config.add_route(
        "content_item_selection",
        "/content_item_selection",
        factory="lms.resources.LTILaunchResource",
    )

    config.add_route("api.sync", "/api/sync", request_method="POST")
    config.add_route("api.grant_token", "/api/grant_token", request_method="GET")

    config.add_route("api.assignments.create", "/api/assignment", request_method="POST")

    # The gateway end-point is a bit of an oddball as it uses LTI launch as the
    # authentication method, and so requires the LTILaunch resource
    config.add_route(
        "api.gateway.h.lti",
        "/api/gateway/h/lti",
        request_method="POST",
        factory="lms.resources.LTILaunchResource",
    )

    config.add_route(
        "blackboard_api.oauth.authorize",
        "/api/blackboard/oauth/authorize",
        factory="lms.resources.OAuth2RedirectResource",
    )
    config.add_route(
        "blackboard_api.oauth.callback",
        "/api/blackboard/oauth/callback",
        factory="lms.resources.OAuth2RedirectResource",
    )
    config.add_route("blackboard_api.oauth.refresh", "/api/blackboard/oauth/refresh")
    config.add_route(
        "blackboard_api.courses.files.list", "/api/blackboard/courses/{course_id}/files"
    )
    config.add_route(
        "blackboard_api.courses.folders.files.list",
        "/api/blackboard/courses/{course_id}/folders/{folder_id}/files",
    )
    config.add_route(
        "blackboard_api.files.via_url", "/api/blackboard/courses/{course_id}/via_url"
    )
    config.add_route(
        "blackboard_api.courses.group_sets.list",
        "/api/blackboard/courses/{course_id}/group_sets",
    )

    config.add_route(
        "onedrive.filepicker.redirect_uri", "/onedrive/filepicker/redirect"
    )
    config.add_route(
        "onedrive.filepicker.verify_domain",
        "/.well-known/microsoft-identity-association.json",
    )

    config.add_route(
        "canvas_api.oauth.authorize",
        "/api/canvas/oauth/authorize",
        factory="lms.resources.OAuth2RedirectResource",
    )
    config.add_route(
        # Unfortunately we can't easily fix this URL to match the others as its
        # been given out to Canvas instances
        "canvas_api.oauth.callback",
        "/canvas_oauth_callback",
        factory="lms.resources.OAuth2RedirectResource",
    )
    config.add_route("canvas_api.oauth.refresh", "/api/canvas/oauth/refresh")
    config.add_route(
        "canvas_api.courses.files.list", "/api/canvas/courses/{course_id}/files"
    )
    config.add_route(
        "canvas_api.files.via_url",
        "/api/canvas/assignments/{resource_link_id}/via_url",
    )
    config.add_route(
        "canvas_api.courses.group_sets.list",
        "/api/canvas/courses/{course_id}/group_sets",
    )

    config.add_route("lti_api.submissions.record", "/api/lti/submissions")
    config.add_route("lti_api.result.read", "/api/lti/result", request_method="GET")
    config.add_route("lti_api.result.record", "/api/lti/result", request_method="POST")

    # JSTOR article IDs need a custom pattern because they may contain a slash,
    # after URL-decoding of the path.
    jstor_article_id_pat = r"(10\.[0-9]+/)?[^/]+"
    config.add_route(
        "jstor_api.articles.metadata",
        f"/api/jstor/articles/{{article_id:{jstor_article_id_pat}}}",
    )
    config.add_route(
        "jstor_api.articles.thumbnail",
        f"/api/jstor/articles/{{article_id:{jstor_article_id_pat}}}/thumbnail",
    )

    config.add_route("vitalsource_api.books.info", "/api/vitalsource/books/{book_id}")
    config.add_route(
        "vitalsource_api.books.toc", "/api/vitalsource/books/{book_id}/toc"
    )
    config.add_route("vitalsource_api.launch_url", "/api/vitalsource/launch_url")

    config.add_route("admin.index", "/admin/")
    config.add_route("admin.instances", "/admin/instances/")
    config.add_route("admin.instances.search", "/admin/instances/search")
    config.add_route("admin.instance.downgrade", "/admin/instance/id/{id_}/downgrade")
    config.add_route("admin.instance.consumer_key", "/admin/instance/{consumer_key}/")
    config.add_route("admin.instance.id", "/admin/instance/id/{id_}/")
    config.add_route(
        "admin.instance.new.registration", "/admin/instance/new/registration"
    )

    config.add_route("admin.organization", "/admin/org/{id_}")
    config.add_route("admin.organizations", "/admin/orgs")
    config.add_route("admin.organization.new", "/admin/org")

    config.add_route("admin.registrations", "/admin/registrations/")
    config.add_route("admin.registrations.search", "/admin/registrations/search")
    config.add_route("admin.registration.id", "/admin/registration/id/{id_}/")
    config.add_route(
        "admin.registration.new.instance", "/admin/registration/id/{id_}/new/instance"
    )
    config.add_route(
        "admin.registration.upgrade.instance",
        "/admin/registration/id/{id_}/upgrade/instance",
    )
    config.add_route("admin.registration.new", "/admin/registration")
    config.add_route("admin.registration.suggest_urls", "/admin/registration/urls")

    config.add_route("lti.oidc", "/lti/1.3/oidc")
    config.add_route("lti.jwks", "/lti/1.3/jwks")
    config.add_route(
        "lti.v13.deep_linking.form_fields", "/lti/1.3/deep_linking/form_fields"
    )
    config.add_route(
        "lti.v11.deep_linking.form_fields", "/lti/1.1/deep_linking/form_fields"
    )
