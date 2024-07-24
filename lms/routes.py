def includeme(config):  # noqa: PLR0915
    config.add_route("index", "/")
    config.add_route("welcome", "/welcome")  # Legacy view, points to "/" now
    config.add_route("feature_flags_test", "/flags/test")
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
        "edit_assignment",
        "/assignment/edit",
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
    config.add_route(
        "lti.reconfigure",
        "/lti/reconfigure",
        factory="lms.resources.LTILaunchResource",
    )
    config.add_route("lti.oidc", "/lti/1.3/oidc")
    config.add_route("lti.jwks", "/lti/1.3/jwks")
    config.add_route(
        "lti.v13.deep_linking.form_fields", "/lti/1.3/deep_linking/form_fields"
    )
    config.add_route(
        "lti.v11.deep_linking.form_fields", "/lti/1.1/deep_linking/form_fields"
    )

    config.add_route("api.sync", "/api/sync", request_method="POST")
    config.add_route(
        "api.courses.group_sets.list", "/api/courses/{course_id}/group_sets"
    )
    config.add_route("api.grant_token", "/api/grant_token", request_method="GET")

    config.add_route("api.assignments.create", "/api/assignment", request_method="POST")

    config.add_route(
        "d2l_api.oauth.authorize",
        "/api/d2l/oauth/authorize",
        factory="lms.resources.OAuth2RedirectResource",
    )
    config.add_route(
        "d2l_api.oauth.callback",
        "/api/d2l/oauth/callback",
        factory="lms.resources.OAuth2RedirectResource",
    )
    config.add_route("d2l_api.oauth.refresh", "/api/d2l/oauth/refresh")
    config.add_route("d2l_api.courses.files.list", "/api/d2l/courses/{course_id}/files")
    config.add_route(
        "d2l_api.courses.files.via_url", "/api/d2l/courses/{course_id}/via_url"
    )

    config.add_route(
        "moodle_api.courses.files.list", "/api/moodle/courses/{course_id}/files"
    )
    config.add_route(
        "moodle_api.courses.files.via_url", "/api/moodle/courses/{course_id}/via_url"
    )
    config.add_route(
        "moodle_api.courses.pages.list", "/api/moodle/courses/{course_id}/pages"
    )
    config.add_route("moodle_api.pages.via_url", "/api/moodle/pages/via_url")
    config.add_route("moodle_api.pages.proxy", "/api/moodle/pages/proxy")

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
    config.add_route("lti_api.submissions.record", "/api/lti/submissions")
    config.add_route("lti_api.result.read", "/api/lti/result", request_method="GET")
    config.add_route("lti_api.result.record", "/api/lti/result", request_method="POST")

    config.add_route(
        "canvas_api.courses.pages.list", "/api/canvas/courses/{course_id}/pages"
    )
    config.add_route("canvas_api.pages.via_url", "/api/canvas/pages/via_url")
    config.add_route("canvas_api.pages.proxy", "/api/canvas/pages/proxy")

    config.add_route(
        "canvas_studio_api.oauth.authorize", "/api/canvas_studio/oauth/authorize"
    )
    config.add_route(
        "canvas_studio_api.oauth.callback", "/api/canvas_studio/oauth/callback"
    )
    config.add_route(
        "canvas_studio_api.oauth.refresh", "/api/canvas_studio/oauth/refresh"
    )
    config.add_route(
        "canvas_studio_api.oauth.refresh_admin",
        "/api/canvas_studio/oauth/refresh_admin",
    )
    config.add_route("canvas_studio_api.media.list", "/api/canvas_studio/media")
    config.add_route(
        "canvas_studio_api.collections.media.list",
        "/api/canvas_studio/collections/{collection_id}/media",
    )
    config.add_route("canvas_studio_api.via_url", "/api/canvas_studio/via_url")

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
    config.add_route("vitalsource_api.document_url", "/api/vitalsource/document_url")
    config.add_route("vitalsource_api.launch_url", "/api/vitalsource/launch_url")

    config.add_route("youtube_api.videos", "/api/youtube/videos/{video_id}")

    config.add_route("email.preferences", "/email/preferences")
    config.add_route("email.unsubscribe", "/email/unsubscribe")
    config.add_route("email.unsubscribed", "/email/unsubscribed")

    config.add_route("admin.index", "/admin/")

    config.add_route("admin.instance.search", "/admin/instances/")
    config.add_route("admin.instance.create", "/admin/instances/create")
    config.add_route("admin.instance.upgrade", "/admin/instances/upgrade")
    config.add_route("admin.instance", "/admin/instances/{id_}/")
    config.add_route("admin.instance.downgrade", "/admin/instances/{id_}/downgrade")
    config.add_route("admin.instance.move_org", "/admin/instances/{id_}/move_org")
    config.add_route(
        "admin.instance.section",
        "/admin/instances/{id_}/{section:info|settings|role-overrides|danger}",
    )

    config.add_route(
        "admin.role.override.new", "/admin/instances/{id_}/role/overrides/new"
    )
    config.add_route("admin.role.override", "/admin/roles/overrides/{id_}")
    config.add_route(
        "admin.role.override.delete", "/admin/roles/overrides/{id_}/delete"
    )

    config.add_route("admin.organization", "/admin/orgs/{id_}")
    config.add_route(
        "admin.organization.section",
        "/admin/orgs/{id_}/{section:info|usage|danger|dashboard-admins}",
    )
    config.add_route("admin.organization.toggle", "/admin/orgs/{id_}/toggle")
    config.add_route("admin.organizations", "/admin/orgs")
    config.add_route("admin.organization.move_org", "/admin/orgs/{id_}/move_org")
    config.add_route("admin.organization.new", "/admin/org/new")
    config.add_route(
        "admin.organization.dashboard_admins.delete",
        "/admin/org{id_}/dashboard-admins/{dashboard_admin_id}/delete",
    )

    config.add_route("admin.registrations", "/admin/registrations/")
    config.add_route("admin.registrations.search", "/admin/registrations/search")
    config.add_route("admin.registration.id", "/admin/registrations/id/{id_}/")
    config.add_route(
        "admin.registration.new.instance", "/admin/registrations/id/{id_}/new/instance"
    )
    config.add_route("admin.registration.new", "/admin/registrations")
    config.add_route("admin.registration.suggest_urls", "/admin/registrations/urls")

    config.add_route("admin.courses", "/admin/courses")
    config.add_route("admin.course", "/admin/courses/{id_}")
    config.add_route("admin.courses.dashboard", "/admin/courses/{id_}/dashboard")

    config.add_route("admin.assignment", "/admin/assignments/{id_}")
    config.add_route("admin.assignment.dashboard", "/admin/assignments/{id_}/dashboard")

    config.add_route("admin.email", "/admin/email")
    config.add_route(
        "admin.email.preview.instructor_email_digest",
        "/admin/email/preview/instructor-email-digest",
    )

    config.add_route(
        "dashboard.launch.assignment", "/dashboard/launch/assignments/{assignment_id}"
    )

    config.add_route(
        "dashboard.assignment",
        "/dashboard/assignments/{assignment_id}",
        factory="lms.resources.dashboard.DashboardResource",
    )
    config.add_route(
        "dashboard.course",
        "/dashboard/courses/{course_id}",
        factory="lms.resources.dashboard.DashboardResource",
    )

    config.add_route(
        "dashboard", "/dashboard", factory="lms.resources.dashboard.DashboardResource"
    )

    config.add_route("api.dashboard.courses.metrics", "/api/dashboard/courses/metrics")
    config.add_route("api.dashboard.courses", "/api/dashboard/courses")
    config.add_route("api.dashboard.course", r"/api/dashboard/courses/{course_id}")

    config.add_route(
        "api.dashboard.assignment", r"/api/dashboard/assignments/{assignment_id}"
    )
    config.add_route("api.dashboard.assignments", "/api/dashboard/assignments")
    config.add_route(
        "api.dashboard.course.assignments.metrics",
        r"/api/dashboard/courses/{course_id}/assignments/metrics",
    )

    config.add_route("api.dashboard.students", "/api/dashboard/students")
    config.add_route(
        "api.dashboard.students.metrics", "/api/dashboard/students/metrics"
    )
