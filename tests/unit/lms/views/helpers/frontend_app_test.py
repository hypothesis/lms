from unittest import mock

import pytest

from lms.models import GradingInfo
from lms.values import LTIUser
from lms.views.helpers import frontend_app


class TestConfigureGrading:
    def test_it_doesnt_enable_grading_if_user_is_not_instructor(self, grading_request):
        js_config = {}
        grading_request.lti_user = LTIUser(
            "TEST_USER_ID", "TEST_OAUTH_CONSUMER_KEY", "student"
        )

        frontend_app.configure_grading(grading_request, js_config)

        assert "lmsGrader" not in js_config

    def test_it_doesnt_enable_grading_if_grading_is_disabled_for_assignment(
        self, grading_request
    ):
        js_config = {}
        del grading_request.params["lis_outcome_service_url"]

        frontend_app.configure_grading(grading_request, js_config)

        assert "lmsGrader" not in js_config

    def test_it_enables_grading(self, grading_request, grading_info_service):
        js_config = {}

        frontend_app.configure_grading(grading_request, js_config)

        assert js_config["lmsGrader"] is True
        grading_info_service.get_by_assignment.assert_called_once_with(
            oauth_consumer_key=grading_request.lti_user.oauth_consumer_key,
            context_id=grading_request.params["context_id"],
            resource_link_id=grading_request.params["resource_link_id"],
        )
        assert js_config["grading"] == {
            "courseName": "Test Course 101",
            "assignmentName": "How to use Hypothesis",
            "students": [
                {
                    "LISOutcomeServiceUrl": f"test_lis_outcomes_service_url_{i}",
                    "LISResultSourcedId": f"test_lis_result_sourcedid_{i}",
                    "displayName": f"test_h_display_name_{i}",
                    "userid": f"acct:test_h_username_{i}@TEST_AUTHORITY",
                }
                for i in range(3)
            ],
        }

    @pytest.fixture
    def grading_info_service(self, grading_info_service):
        grading_info_service.get_by_assignment.return_value = [
            mock.create_autospec(
                GradingInfo,
                instance=True,
                spec_set=True,
                lis_result_sourcedid=f"test_lis_result_sourcedid_{i}",
                lis_outcome_service_url=f"test_lis_outcomes_service_url_{i}",
                h_username=f"test_h_username_{i}",
                h_display_name=f"test_h_display_name_{i}",
            )
            for i in range(3)
        ]
        return grading_info_service

    @pytest.fixture
    def grading_request(self, pyramid_request):
        pyramid_request.params[
            "tool_consumer_info_product_family_code"
        ] = "MyFakeLTITool"
        pyramid_request.params[
            "lis_outcome_service_url"
        ] = "https://myfakeltitool.hypothes.is/grades"

        pyramid_request.lti_user = LTIUser(
            "TEST_USER_ID", "TEST_OAUTH_CONSUMER_KEY", "instructor"
        )
        pyramid_request.params["context_id"] = "unique_course_id"
        pyramid_request.params["context_title"] = "Test Course 101"
        pyramid_request.params["resource_link_id"] = "unique_assignment_id"
        pyramid_request.params["resource_link_title"] = "How to use Hypothesis"
        return pyramid_request


pytestmark = pytest.mark.usefixtures("grading_info_service")
