from unittest import mock

import pytest

from lms.models import LISResultSourcedId
from lms.services.lis_result_sourcedid import LISResultSourcedIdService
from lms.values import LTIUser
from lms.views.helpers import frontend_app


@pytest.mark.usefixtures("lis_result_sourcedid_svc")
class TestConfigureGrading:
    def test_it_sets_grading_config_if_qualified_request(self, grading_request):
        js_config = {}

        frontend_app.configure_grading(grading_request, js_config)

        assert "lmsGrader" in js_config

    def test_it_does_not_set_grading_config_if_unqualified_request(
        self, pyramid_request
    ):
        js_config = {}

        frontend_app.configure_grading(pyramid_request, js_config)

        assert "lmsGrader" not in js_config

    def test_it_fetches_lis_student_records(
        self, grading_request, lis_result_sourcedid_svc
    ):
        frontend_app.configure_grading(grading_request, {})

        lis_result_sourcedid_svc.fetch_students_by_assignment.assert_called_once_with(
            oauth_consumer_key=grading_request.lti_user.oauth_consumer_key,
            context_id=grading_request.params["context_id"],
            resource_link_id=grading_request.params["resource_link_id"],
        )

    def test_it_sets_list_of_students_on_config(self, grading_request):
        js_config = {}

        frontend_app.configure_grading(grading_request, js_config)

        assert "students" in js_config["grading"]
        assert js_config["grading"]["students"] == []

    def test_it_sets_js_properties_for_each_student_record(
        self, lis_result_sourcedid_svc, lis_result_sourcedids, grading_request
    ):
        js_config = {}
        lis_result_sourcedid_svc.fetch_students_by_assignment.return_value = (
            lis_result_sourcedids
        )

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
def lis_result_sourcedid_svc(pyramid_config):
    svc = mock.create_autospec(LISResultSourcedIdService, instance=True)
    pyramid_config.register_service(svc, name="lis_result_sourcedid")
    svc.fetch_students_by_assignment.return_value = []
    return svc


@pytest.fixture
def lis_result_sourcedids():
    lis_result_1 = LISResultSourcedId(
        h_username="foobar",
        h_display_name="A Student",
        lis_result_sourcedid="sourcedid_1",
        lis_outcome_service_url="http://fakeo",
    )

    lis_result_2 = LISResultSourcedId(
        h_username="deadbeef",
        h_display_name="Another Student",
        lis_result_sourcedid="sourcedid_2",
        lis_outcome_service_url="http://fakeo",
    )

    lis_result_3 = LISResultSourcedId(
        h_username="feedbee",
        h_display_name="Yet More Student",
        lis_result_sourcedid="sourcedid_3",
        lis_outcome_service_url="http://fakeo",
    )
    return [lis_result_1, lis_result_2, lis_result_3]


@pytest.fixture
def grading_request(pyramid_request):
    pyramid_request.params["tool_consumer_info_product_family_code"] = "BlackboardLearn"
    pyramid_request.lti_user = LTIUser(
        "TEST_USER_ID", "TEST_OAUTH_CONSUMER_KEY", "instructor"
    )
    pyramid_request.params["context_id"] = "unique_course_id"
    pyramid_request.params["context_title"] = "Test Course 101"
    pyramid_request.params["resource_link_id"] = "unique_assignment_id"
    pyramid_request.params["resource_link_title"] = "How to use Hypothesis"
    return pyramid_request
