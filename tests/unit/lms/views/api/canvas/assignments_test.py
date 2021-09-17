import pytest

from lms.views.api.canvas.assignments import AssignmentsAPIViews


class TestAssignmentsAPIViews:
    @pytest.mark.parametrize(
        "request_body,expected_url,expected_extra",
        [
            (
                {
                    "content": {"type": "url", "url": "https://example.com"},
                    "ext_lti_assignment_id": "EXT_LTI_ASSIGNMENT_ID",
                },
                "https://example.com",
                {},
            ),
            (
                {
                    "content": {
                        "type": "url",
                        "url": "https://drive.google.com/uc?id=DRIVE_ID&export=download",
                    },
                    "ext_lti_assignment_id": "EXT_LTI_ASSIGNMENT_ID",
                },
                "https://drive.google.com/uc?id=DRIVE_ID&export=download",
                {},
            ),
            (
                {
                    "content": {
                        "type": "file",
                        "file": {
                            "size": 205792,
                            "display_name": "A Third File.pdf",
                            "id": 652,
                            "updated_at": "2021-05-17T15:15:47Z",
                        },
                    },
                    "ext_lti_assignment_id": "EXT_LTI_ASSIGNMENT_ID",
                    "course_id": "COURSE_ID",
                },
                "canvas://file/course/COURSE_ID/file_id/652",
                {
                    "canvas_file": {
                        "size": 205792,
                        "display_name": "A Third File.pdf",
                        "id": 652,
                        "updated_at": "2021-05-17T15:15:47Z",
                    }
                },
            ),
        ],
    )
    def test_create(
        self,
        application_instance_service,
        assignment_service,
        pyramid_request,
        request_body,
        expected_url,
        expected_extra,
    ):
        pyramid_request.parsed_params = request_body

        result = AssignmentsAPIViews(pyramid_request).create()

        assignment_service.set_document_url.assert_called_once_with(
            application_instance_service.get.return_value.tool_consumer_instance_guid,
            expected_url,
            ext_lti_assignment_id="EXT_LTI_ASSIGNMENT_ID",
            extra=expected_extra,
        )
        assert result == {
            "ext_lti_assignment_id": assignment_service.set_document_url.return_value.ext_lti_assignment_id
        }

    @pytest.mark.usefixtures("application_instance_service", "assignment_service")
    def test_create_unkown_type(
        self,
        pyramid_request,
    ):
        pyramid_request.parsed_params = {
            "content": {"type": "nothing"},
            "ext_lti_assignment_id": "EXT_LTI_ASSIGNMENT_ID",
            "course_id": "COURSE_ID",
        }

        with pytest.raises(ValueError):
            AssignmentsAPIViews(pyramid_request).create()
