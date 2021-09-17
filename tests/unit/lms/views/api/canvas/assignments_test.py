import pytest

from lms.views.api.canvas.assignments import AssignmentsAPIViews


class TestAssignmentsAPIViews:
    @pytest.mark.parametrize(
        "content_json,expected_url,expected_extra",
        [
            ({"type": "url", "url": "https://example.com"}, "https://example.com", {}),
            (
                {
                    "type": "url",
                    "url": "https://drive.google.com/uc?id=DRIVE_ID&export=download",
                },
                "https://drive.google.com/uc?id=DRIVE_ID&export=download",
                {},
            ),
            (
                {
                    "type": "file",
                    "file": {
                        "size": 205792,
                        "display_name": "A Third File.pdf",
                        "id": 652,
                        "updated_at": "2021-05-17T15:15:47Z",
                    },
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
        content_json,
        expected_url,
        expected_extra,
    ):
        # {type: "url", url: "https://example.com"}
        # {type: "url", url: "https://drive.google.com/uc?id=1-YXZ_kapYjMh_iYX9I6PfkZHa8waUJOS&export=download"}
        # {type: "file", file: {…}}
        # {size: 205792, display_name: "A Third File.pdf", id: 652, updated_at: "2021-05-17T15:15:47Z"##}
        pyramid_request.parsed_params = {
            "content": content_json,
            "ext_lti_assignment_id": "EXT_LTI_ASSIGNMENT_ID",
            "course_id": "COURSE_ID",
        }

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
