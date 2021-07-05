import pytest

from lms.views.api.canvas.files import FilesAPIViews


@pytest.mark.usefixtures(
    "application_instance_service", "assignment_service", "canvas_service"
)
class TestFilesAPIViews:
    def test_list_files(self, canvas_service, pyramid_request):
        pyramid_request.matchdict = {"course_id": "test_course_id"}

        result = FilesAPIViews(pyramid_request).list_files()

        assert result == canvas_service.api.list_files.return_value
        canvas_service.api.list_files.assert_called_once_with("test_course_id")

    @pytest.mark.usefixtures("with_teacher_or_student")
    def test_via_url(
        self,
        pyramid_request,
        application_instance_service,
        assignment_service,
        canvas_service,
        helpers,
    ):
        application_instance = application_instance_service.get.return_value
        module_item_configuration = assignment_service.get.return_value
        pyramid_request.matchdict = {
            "course_id": "test_course_id",
            "file_id": "test_file_id",
            "resource_link_id": "test_resource_link_id",
        }

        result = FilesAPIViews(pyramid_request).via_url()

        assignment_service.get.assert_called_once_with(
            application_instance.tool_consumer_instance_guid,
            "test_resource_link_id",
        )
        canvas_service.public_url_for_file.assert_called_once_with(
            module_item_configuration,
            "test_file_id",
            "test_course_id",
            check_in_course=pyramid_request.lti_user.is_instructor,
        )
        helpers.via_url.assert_called_once_with(
            pyramid_request,
            canvas_service.public_url_for_file.return_value,
            content_type="pdf",
        )
        assert result == {"via_url": helpers.via_url.return_value}

    @pytest.fixture(params=("instructor", "learner"))
    def with_teacher_or_student(self, request, pyramid_request):
        pyramid_request.lti_user._replace(roles=request.param)

    @pytest.fixture
    def helpers(self, patch):
        return patch("lms.views.api.canvas.files.helpers")
