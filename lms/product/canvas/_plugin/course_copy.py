from lms.product.plugin.course_copy import CourseCopyPlugin


class CanvasCourseCopyPlugin(CourseCopyPlugin):

    file_type = "canvas_file"

    def _store_new_course_files(self, course_id):
        return self._api.list_files(course_id)

    @classmethod
    def factory(cls, _context, request):
        return cls(
            api=request.find_service(name="canvas_api_client"),
            file_service=request.find_service(name="file"),
        )
