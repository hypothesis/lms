from unittest import mock

import pytest

from lms.services import HAPIError
from lms.services.h_api_client import HAPIClient
from lms.values import HUser
from lms.views.basic_lti_launch import BasicLTILaunchViews


class TestBasicLTILaunch:
    """
    Test behavior common to all LTI launches.
    """

    def test_it_configures_frontend(self, context, pyramid_request):
        BasicLTILaunchViews(context, pyramid_request)
        assert context.js_config["mode"] == "basic-lti-launch"

    def test_it_does_not_configure_grading_if_request_unqualified(
        self, context, pyramid_request
    ):
        BasicLTILaunchViews(context, pyramid_request)
        assert "lmsGrader" not in context.js_config

    def test_it_adds_report_submission_config_if_required_params_present(
        self, context, pyramid_request, lti_outcome_params
    ):
        pyramid_request.params.update(lti_outcome_params)

        BasicLTILaunchViews(context, pyramid_request)

        assert context.js_config["submissionParams"] == {
            "h_username": context.h_user.username,
            "lis_result_sourcedid": "modelstudent-assignment1",
            "lis_outcome_service_url": "https://hypothesis.shinylms.com/outcomes",
        }

    @pytest.mark.parametrize(
        "key",
        [
            "lis_result_sourcedid",
            "lis_outcome_service_url",
            "tool_consumer_info_product_family_code",
        ],
    )
    def test_it_doesnt_add_report_submission_config_if_required_param_missing(
        self, context, pyramid_request, lti_outcome_params, key
    ):
        pyramid_request.params.update(lti_outcome_params)
        del pyramid_request.params[key]

        BasicLTILaunchViews(context, pyramid_request)

        assert "submissionParams" not in context.js_config

    def test_it_adds_report_submission_config_if_lms_not_canvas(
        self, context, pyramid_request, lti_outcome_params
    ):
        pyramid_request.params.update(lti_outcome_params)
        pyramid_request.params.update(
            {"tool_consumer_info_product_family_code": "whiteboard"}
        )

        BasicLTILaunchViews(context, pyramid_request)

        assert "submissionParams" not in context.js_config

    def test_it_configures_client_to_focus_on_user_if_param_set(
        self, context, pyramid_request, h_api_client
    ):
        context.hypothesis_config = {}
        pyramid_request.params.update({"focused_user": "user123"})
        h_api_client.get_user.return_value = HUser(
            authority="TEST_AUTHORITY", username="user123", display_name="Jim Smith"
        )

        BasicLTILaunchViews(context, pyramid_request)

        h_api_client.get_user.assert_called_once_with("user123")
        assert context.hypothesis_config["focus"] == {
            "user": {"username": "user123", "displayName": "Jim Smith"}
        }

    def test_it_uses_placeholder_display_name_for_focused_user_if_api_call_fails(
        self, context, pyramid_request, h_api_client
    ):
        context.hypothesis_config = {}
        pyramid_request.params.update({"focused_user": "user123"})
        h_api_client.get_user.side_effect = HAPIError("User does not exist")

        BasicLTILaunchViews(context, pyramid_request)

        h_api_client.get_user.assert_called_once_with("user123")
        assert context.hypothesis_config["focus"] == {
            "user": {
                "username": "user123",
                "displayName": "(Couldn't fetch student name)",
            }
        }

    @pytest.fixture
    def h_api_client(self, pyramid_config):
        svc = mock.create_autospec(HAPIClient, instance=True)
        pyramid_config.register_service(svc, name="h_api_client")
        return svc
