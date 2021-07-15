class FilePickerConfig:
    """Config generation for specific file pickers."""

    @classmethod
    def blackboard_config(cls, _context, request, application_instance):
        """Get Blackboard files config."""

        enabled = application_instance.settings.get("blackboard", "files_enabled")

        auth_url = request.route_url("blackboard_api.oauth.authorize")
        course_id = request.params.get("context_id")

        return {
            "enabled": enabled,
            "listFiles": {
                "authUrl": auth_url,
                "path": request.route_path(
                    "blackboard_api.courses.files.list", course_id=course_id
                ),
            },
        }

    @classmethod
    def canvas_config(cls, context, request, application_instance):
        """Get Canvas files config."""

        enabled = context.is_canvas and (
            "custom_canvas_course_id" in request.params
            and application_instance.developer_key is not None
        )

        auth_url = request.route_url("canvas_api.oauth.authorize")
        course_id = request.params.get("custom_canvas_course_id")

        return {
            "enabled": enabled,
            "groupsEnabled": context.canvas_groups_enabled,
            # The "content item selection" that we submit to Canvas's
            # content_item_return_url is actually an LTI launch URL with
            # the selected document URL or file_id as a query parameter. To
            # construct these launch URLs our JavaScript code needs the
            # base URL of our LTI launch endpoint.
            "ltiLaunchUrl": request.route_url("lti_launches"),
            "listFiles": {
                "authUrl": auth_url,
                "path": request.route_path(
                    "canvas_api.courses.files.list", course_id=course_id
                ),
            },
            "listGroupSets": {
                "authUrl": auth_url,
                "path": request.route_path(
                    "canvas_api.courses.group_sets.list", course_id=course_id
                ),
            },
        }

    @classmethod
    def google_files_config(cls, context, request, application_instance):
        """Get Google file picker config."""

        # Get the URL of the top-most page that the LMS app is running in.
        #
        # The frontend has to pass this to Google Picker, otherwise Google
        # Picker refuses to launch in an iframe.
        origin = context.custom_canvas_api_domain or application_instance.lms_url

        return {
            "clientId": request.registry.settings["google_client_id"],
            "developerKey": request.registry.settings["google_developer_key"],
            "origin": origin,
        }

    @classmethod
    def microsoft_onedrive(cls, _context, request, application_instance):
        enabled = application_instance.settings.get(
            "microsoft_onedrive", "files_enabled"
        )
        if not enabled:
            return {"enabled": False}

        return {
            "enabled": True,
            "clientId": request.registry.settings["onedrive_client_id"],
            "redirectURI": request.route_url("onedrive.filepicker.authorize"),
        }

    @classmethod
    def vital_source_config(cls, _context, request, _application_instance):
        """Get Vital Source config."""

        return {"enabled": request.feature("vitalsource")}
