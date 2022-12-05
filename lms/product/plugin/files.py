class FilesPlugin:
    """Abstraction over the integration with the LMS provided file storage."""

    missing_files_help_link = None

    def enabled(self, request, _application_instance) -> bool:
        return request.product.settings.files_enabled

    def list_files_config(self, request) -> dict:
        return {
            "authUrl": request.route_url(request.product.route.oauth2_authorize),
            "path": request.route_path(
                request.product.route.list_course_files,
                course_id=request.lti_params.get("context_id"),
            ),
        }
