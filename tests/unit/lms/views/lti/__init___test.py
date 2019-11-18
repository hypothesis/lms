from unittest import mock

import pytest

from lms.services import HAPIError
from lms.services.h_api_client import HAPIClient
from lms.values import HUser
from lms.views.lti import LTIViewBaseClass


class TestLTIViewBaseClass:
    """
    Test behavior common to all LTI launches.
    """

    def test_it_configures_frontend(self, context, pyramid_request):
        LTIViewBaseClass(context, pyramid_request)
        assert context.js_config["mode"] == "basic-lti-launch"

    def test_it_adds_report_submission_config_if_required_params_present(
        self, context, pyramid_request, lti_outcome_params
    ):
        pyramid_request.params.update(lti_outcome_params)

        LTIViewBaseClass(context, pyramid_request)

        assert context.js_config["submissionParams"] == {
            "h_username": context.h_user.username,
            "lis_result_sourcedid": "modelstudent-assignment1",
            "lis_outcome_service_url": "https://hypothesis.shinylms.com/outcomes",
        }

    @pytest.mark.parametrize(
        "key,value",
        [
            ("lis_result_sourcedid", None),
            ("lis_outcome_service_url", None),
            ("tool_consumer_info_product_family_code", None),
            # Anything non canvas should do here
            ("tool_consumer_info_product_family_code", "whiteboard"),
        ],
    )
    def test_it_doesnt_add_report_submission_config_if_required_param_wrong(
        self, context, pyramid_request, lti_outcome_params, key, value
    ):
        pyramid_request.params.update(lti_outcome_params)
        if value is None:
            del pyramid_request.params[key]
        else:
            pyramid_request.params[key] = value

        LTIViewBaseClass(context, pyramid_request)

        assert "submissionParams" not in context.js_config

    def test_it_configures_client_to_focus_on_user_if_param_set(
        self, context, pyramid_request, h_api_client
    ):
        context.hypothesis_config = {}
        pyramid_request.params.update({"focused_user": "user123"})
        h_api_client.get_user.return_value = HUser(
            authority="TEST_AUTHORITY", username="user123", display_name="Jim Smith"
        )

        LTIViewBaseClass(context, pyramid_request)

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

        LTIViewBaseClass(context, pyramid_request)

        h_api_client.get_user.assert_called_once_with("user123")
        assert context.hypothesis_config["focus"] == {
            "user": {
                "username": "user123",
                "displayName": "(Couldn't fetch student name)",
            }
        }

    def test_set_submission_param_adds_param_if_submissionParams_present(
        self, context, pyramid_request
    ):
        context.js_config = {"submissionParams": {}}

        base_class = LTIViewBaseClass(context, pyramid_request)
        base_class.set_submission_param(mock.sentinel.key, mock.sentinel.value)

        assert (
            context.js_config["submissionParams"][mock.sentinel.key]
            == mock.sentinel.value
        )

    def test_set_submission_param_does_not_add_param_if_submissionParams_missing(
        self, context, pyramid_request
    ):
        context.js_config = {}
        base_class = LTIViewBaseClass(context, pyramid_request)

        base_class.set_submission_param(mock.sentinel.key, mock.sentinel.value)

        assert context.js_config.get("submissionParams") is None

    def test_set_via_url_configures_as_expected(
        self, context, pyramid_request, via_url
    ):
        document_url = mock.sentinel.document_url
        context.js_config = {"submissionParams": {}, "urls": {}}
        base_class = LTIViewBaseClass(context, pyramid_request)

        base_class.set_via_url(document_url)

        via_url.assert_called_once_with(pyramid_request, document_url)
        assert context.js_config["urls"]["via_url"] == via_url.return_value
        assert context.js_config["submissionParams"]["document_url"] == document_url

    @pytest.fixture
    def h_api_client(self, pyramid_config):
        svc = mock.create_autospec(HAPIClient, instance=True)
        pyramid_config.register_service(svc, name="h_api_client")
        return svc
