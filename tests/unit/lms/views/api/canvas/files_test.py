import pytest

from lms.views.api.canvas.files import FilesAPIViews


@pytest.mark.usefixtures("canvas_service")
class TestFilesAPIViews:
    def test_list_files(self, canvas_service, pyramid_request):
        pyramid_request.matchdict = {"course_id": "test_course_id"}

        result = FilesAPIViews(pyramid_request).list_files()

        assert result == canvas_service.api.list_files.return_value
        canvas_service.api.list_files.assert_called_once_with("test_course_id")

    def test_via_url(self, pyramid_request, canvas_service, helpers):
        pyramid_request.matchdict = {
            "course_id": "test_course_id",
            "file_id": "test_file_id",
        }

        result = FilesAPIViews(pyramid_request).via_url()

        assert result["via_url"] == helpers.via_url.return_value

        canvas_service.public_url_for_file.assert_called_once_with(
            file_id="test_file_id",
            course_id="test_course_id",
            check_in_course=pyramid_request.lti_user.is_instructor,
        )

        helpers.via_url.assert_called_once_with(
            pyramid_request,
            canvas_service.public_url_for_file.return_value,
            content_type="pdf",
        )

    @pytest.fixture
    def helpers(self, patch):
        return patch("lms.views.api.canvas.files.helpers")
