from unittest import mock

import pytest

from lms.models import GradingInfo
from lms.services.grading_info import GradingInfoService
from lms.values import LTIUser
from lms.views.helpers import frontend_app


@pytest.mark.usefixtures("grading_info_svc")
class TestConfigureGrading:
    def test_it_enables_grading(self, grading_request):
        js_config = {}

        frontend_app.configure_grading(grading_request, js_config)

        assert "lmsGrader" in js_config

    def test_it_disables_grading_if_user_is_not_instructor(self, grading_request):
        js_config = {}
        grading_request.lti_user = LTIUser(
            "TEST_USER_ID", "TEST_OAUTH_CONSUMER_KEY", "student"
        )

        frontend_app.configure_grading(grading_request, js_config)

        assert "lmsGrader" not in js_config

    def test_it_disables_grading_if_grading_is_disabled_for_assignment(
        self, grading_request
    ):
        js_config = {}
        del grading_request.params["lis_outcome_service_url"]

        frontend_app.configure_grading(grading_request, js_config)

        assert "lmsGrader" not in js_config

    def test_it_fetches_grading_info_records(self, grading_request, grading_info_svc):
        frontend_app.configure_grading(grading_request, {})

        grading_info_svc.get_by_assignment.assert_called_once_with(
            oauth_consumer_key=grading_request.lti_user.oauth_consumer_key,
            context_id=grading_request.params["context_id"],
            resource_link_id=grading_request.params["resource_link_id"],
        )

    def test_it_sets_list_of_grading_info_on_config(self, grading_request):
        js_config = {}

        frontend_app.configure_grading(grading_request, js_config)

        assert "students" in js_config["grading"]
        assert js_config["grading"]["students"] == []

    def test_it_sets_js_properties_for_each_grading_info_record(
        self, grading_info_svc, grading_infos, grading_request
    ):
        js_config = {}
        grading_info_svc.get_by_assignment.return_value = grading_infos

        frontend_app.configure_grading(grading_request, js_config)

        assert len(js_config["grading"]["students"]) == 3
        for propName in [
            "userid",
            "displayName",
            "LISResultSourcedId",
            "LISOutcomeServiceUrl",
        ]:
            assert propName in js_config["grading"]["students"][0]

    def test_it_sets_course_and_assignment_names(self, grading_request):
        js_config = {}
        frontend_app.configure_grading(grading_request, js_config)

        assert js_config["grading"]["courseName"] == "Test Course 101"
        assert js_config["grading"]["assignmentName"] == "How to use Hypothesis"


@pytest.fixture
def grading_info_svc(pyramid_config):
    svc = mock.create_autospec(GradingInfoService, instance=True)
    pyramid_config.register_service(svc, name="grading_info")
    svc.get_by_assignment.return_value = []
    return svc


@pytest.fixture
def grading_infos():
    return [
        GradingInfo(
            h_username=f"username_{index}",
            h_display_name=f"Student {index}",
            lis_result_sourcedid=f"lis_result_sourcedid_{index}",
            lis_outcome_service_url="http://example.com/service_url",
        )
        for index in range(3)
    ]


@pytest.fixture
def grading_request(pyramid_request):
    pyramid_request.params["tool_consumer_info_product_family_code"] = "MyFakeLTITool"
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
