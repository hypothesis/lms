from lms.services import JSTORService, VitalSourceService


class FilePickerConfig:
    """Config generation for specific file pickers."""

    @classmethod
    def lms_files_config(cls, request, application_instance):
        """Get config for the current LMS files integration."""
        product = request.product
        files_enabled = product.plugin.files.enabled(request, application_instance)

        config = {
            "enabled": files_enabled,
            "missingFilesHelpLink": product.plugin.files.missing_files_help_link,
        }

        if files_enabled:
            config["listFiles"] = product.plugin.files.list_files_config(request)

        return config

    @classmethod
    def google_files_config(cls, request, application_instance):
        """Get Google file picker config."""

        return {
            "clientId": request.registry.settings["google_client_id"],
            "developerKey": request.registry.settings["google_developer_key"],
            # Get the URL of the top-most page that the LMS app is running in.
            # The frontend has to pass this to Google Picker, otherwise Google
            # Picker refuses to launch in an iframe.
            "origin": request.lti_params.get(
                "custom_canvas_api_domain", application_instance.lms_url
            ),
        }

    @classmethod
    def microsoft_onedrive(cls, request, application_instance):
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
    def vitalsource_config(cls, request, _application_instance):
        """Get VitalSource config."""

        return {"enabled": request.find_service(VitalSourceService).enabled}

    @classmethod
    def jstor_config(cls, request, _application_instance):
        """Get JSTOR config."""

        return {"enabled": request.find_service(JSTORService).enabled}
