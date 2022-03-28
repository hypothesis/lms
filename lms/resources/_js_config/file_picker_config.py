class FilePickerConfig:
    """Config generation for specific file pickers."""

    @classmethod
    def blackboard_config(cls, context, request, application_instance):
        """Get Blackboard files config."""
        files_enabled = application_instance.settings.get("blackboard", "files_enabled")
        groups_enabled = context.blackboard_groups_enabled

        auth_url = request.route_url("blackboard_api.oauth.authorize")
        course_id = request.lti_params.get("context_id")

        config = {
            "enabled": files_enabled,
            "groupsEnabled": groups_enabled,
        }

        if files_enabled:
            config["listFiles"] = {
                "authUrl": auth_url,
                "path": request.route_path(
                    "blackboard_api.courses.files.list", course_id=course_id
                ),
            }

        if groups_enabled:
            config["listGroupSets"] = {
                "authUrl": auth_url,
                "path": request.route_path(
                    "blackboard_api.courses.group_sets.list", course_id=course_id
                ),
            }

        return config

    @classmethod
    def canvas_config(cls, context, request, application_instance):
        """Get Canvas files config."""
        enabled = context.is_canvas and (
            "custom_canvas_course_id" in request.params
            and application_instance.developer_key is not None
        )
        groups_enabled = context.canvas_groups_enabled

        auth_url = request.route_url("canvas_api.oauth.authorize")
        course_id = request.params.get("custom_canvas_course_id")

        config = {
            "enabled": enabled,
            "groupsEnabled": groups_enabled,
            "listFiles": {
                "authUrl": auth_url,
                "path": request.route_path(
                    "canvas_api.courses.files.list", course_id=course_id
                ),
            },
        }

        if groups_enabled:
            config["listGroupSets"] = {
                "authUrl": auth_url,
                "path": request.route_path(
                    "canvas_api.courses.group_sets.list", course_id=course_id
                ),
            }

        return config

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
            "microsoft_onedrive", "files_enabled", default=True
        )
        if not enabled:
            return {"enabled": False}

        return {
            "enabled": True,
            "clientId": request.registry.settings["onedrive_client_id"],
            "redirectURI": request.route_url("onedrive.filepicker.redirect_uri"),
        }

    @classmethod
    def vital_source_config(cls, _context, _request, application_instance):
        """Get Vital Source config."""
        enabled = application_instance.settings.get("vitalsource", "enabled", False)
        return {"enabled": enabled}

    @classmethod
    def jstor_config(cls, _context, _request, application_instance):
        """Get JSTOR config."""
        enabled = application_instance.settings.get("jstor", "enabled", False)
        return {"enabled": enabled}
