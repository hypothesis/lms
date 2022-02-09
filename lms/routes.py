def includeme(config):
    config.add_route("index", "/")
    config.add_route("feature_flags_test", "/flags/test")
    config.add_route("welcome", "/welcome")
    config.add_route("assets", "/assets/*subpath")
    config.add_route("status", "/_status")
    config.add_route("favicon", "/favicon.ico")
    config.add_route("ui-playground", "/ui-playground/*remainder")

    config.add_route("login", "/login")
    config.add_route("logout", "/logout")
    config.add_route("reports", "/reports")

    config.add_route("config_xml", "/config_xml")
    config.add_route("canvas_config_json", "/canvas/config.json")

    config.add_route("lti_oidc", "/openid/oidc")
    config.add_route("jwts", "/opendid/jwts.json")

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

    config.add_route("api.grant_token", "/api/grant_token", request_method="GET")

    config.add_route("api.assignments.create", "/api/assignment", request_method="POST")

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
    config.add_route("blackboard_api.sync", "/api/blackboard/sync")

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

    config.add_route("canvas_api.sync", "/api/canvas/sync", request_method="POST")

    config.add_route("lti_api.submissions.record", "/api/lti/submissions")
    config.add_route("lti_api.result.read", "/api/lti/result", request_method="GET")
    config.add_route("lti_api.result.record", "/api/lti/result", request_method="POST")

    config.add_route("vitalsource_api.books.info", "/api/vitalsource/books/{book_id}")
    config.add_route(
        "vitalsource_api.books.toc", "/api/vitalsource/books/{book_id}/toc"
    )

    config.add_route("admin.index", "/admin/")
    config.add_route("admin.instances", "/admin/instances/")
    config.add_route("admin.instance", "/admin/instance/{consumer_key}/")
