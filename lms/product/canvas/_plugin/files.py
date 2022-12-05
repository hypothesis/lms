from lms.product.plugin.files import FilesPlugin


class CanvasFilesPlugin(FilesPlugin):
    missing_files_help_link = "https://community.canvaslms.com/t5/Instructor-Guide/How-do-I-upload-a-file-to-a-course/ta-p/618"

    def enabled(self, request, application_instance) -> bool:
        return (
            "custom_canvas_course_id" in request.lti_params
            and application_instance.developer_key is not None
        )

    def list_files_config(self, request) -> dict:
        return {
            "authUrl": request.route_url(request.product.route.oauth2_authorize),
            "path": request.route_path(
                request.product.route.list_course_files,
                course_id=request.lti_params.get("custom_canvas_course_id"),
            ),
        }
