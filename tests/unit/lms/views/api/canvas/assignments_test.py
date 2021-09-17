from lms.views.api.canvas.assignments import AssignmentsAPIViews


class TestAssignmentsAPIViews:
    def test_create(
        self, application_instance_service, assignment_service, pyramid_request
    ):
        pyramid_request.json_body = {
            "content": {
                "url": "https://assignment.com/url",
            },
            "ext_lti_assignment_id": "EXT_LTI_ASSIGNMENT_ID",
        }

        result = AssignmentsAPIViews(pyramid_request).create()

        assignment_service.set_document_url.assert_called_once_with(
            application_instance_service.get.return_value.tool_consumer_instance_guid,
            "https://assignment.com/url",
            ext_lti_assignment_id="EXT_LTI_ASSIGNMENT_ID",
        )
        assert result == {
            "ext_lti_assignment_id": assignment_service.set_document_url.return_value.ext_lti_assignment_id
        }
