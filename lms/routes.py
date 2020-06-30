def includeme(config):
    config.add_route("index", "/")
    config.add_route("feature_flags_test", "/flags/test")
    config.add_route("welcome", "/welcome")
    config.add_route("assets", "/assets/*subpath")
    config.add_route("status", "/_status")
    config.add_route("favicon", "/favicon.ico")

    config.add_route("login", "/login")
    config.add_route("logout", "/logout")
    config.add_route("reports", "/reports")

    config.add_route("config_xml", "/config_xml")
    config.add_route(
        "module_item_configurations",
        "/module_item_configurations",
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
    config.add_route(
        "canvas_oauth_callback",
        "/canvas_oauth_callback",
        factory="lms.resources.CanvasOAuth2RedirectResource",
    )
    config.add_route(
        "canvas_api.authorize",
        "/api/canvas/authorize",
        factory="lms.resources.CanvasOAuth2RedirectResource",
    )
    config.add_route(
        "canvas_api.courses.files.list", "/api/canvas/courses/{course_id}/files"
    )
    config.add_route("canvas_api.files.via_url", "/api/canvas/files/{file_id}/via_url")
    config.add_route("canvas_api.sync", "/api/canvas/sync", request_method="POST")

    config.add_route("lti_api.submissions.record", "/api/lti/submissions")
    config.add_route("lti_api.result.read", "/api/lti/result", request_method="GET")
    config.add_route("lti_api.result.record", "/api/lti/result", request_method="POST")
