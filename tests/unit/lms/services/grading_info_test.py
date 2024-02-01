from unittest import mock

import pytest
from h_matchers import Any

from lms.models import GradingInfo
from lms.resources import LTILaunchResource
from lms.services.grading_info import GradingInfoService
from tests import factories

pytestmark = pytest.mark.usefixtures("application_instance_service")


class TestGetStudentsForGrading:
    @pytest.mark.parametrize("lti_v13", [True, False])
    def test_it(
        self, request, svc, matching_grading_infos, application_instance, lti_v13
    ):
        if lti_v13:
            application_instance = request.getfixturevalue(
                "lti_v13_application_instance"
            )

        students = svc.get_students_for_grading(
            application_instance,
            "matching_context_id",
            "matching_resource_link_id",
            mock.sentinel.grading_url,
        )

        expected_students = [
            {
                "userid": f"acct:{grading_info.h_username}@lms.hypothes.is",
                "displayName": grading_info.h_display_name,
                "lmsId": grading_info.user_id,
                "LISResultSourcedId": (
                    grading_info.lis_result_sourcedid
                    if not lti_v13
                    else grading_info.user_id
                ),
                "LISOutcomeServiceUrl": mock.sentinel.grading_url,
            }
            for grading_info in matching_grading_infos
        ]
        assert sorted(students, key=lambda x: x["userid"]) == sorted(
            expected_students, key=lambda x: x["userid"]
        )

    @pytest.mark.parametrize(
        "filter_application_instance,context_id,resource_link_id",
        [
            (
                None,
                "matching_context_id",
                "matching_resource_link_id",
            ),
            (
                "application_instance",
                "other_context_id",
                "matching_resource_link_id",
            ),
            (
                "application_instance",
                "matching_context_id",
                "other_resource_link_id",
            ),
            ("other_oauth_consumer_key", "other_context_id", "other_resource_link_id"),
        ],
    )
    def test_it_with_no_match(
        self,
        svc,
        filter_application_instance,
        context_id,
        resource_link_id,
        application_instance,
    ):
        grading_infos = svc.get_students_for_grading(
            application_instance if filter_application_instance else None,
            context_id,
            resource_link_id,
            mock.sentinel.grading_url,
        )

        assert not list(grading_infos)

    @pytest.fixture(autouse=True)
    def matching_grading_infos(self, application_instance):
        """Add some GradingInfo's that should match the DB query in the test above."""
        return factories.GradingInfo.create_batch(
            size=3,
            application_instance=application_instance,
            context_id="matching_context_id",
            resource_link_id="matching_resource_link_id",
        )

    @pytest.fixture(autouse=True)
    def noise_grading_infos(self):
        """Add some GradingInfo's that should *not* match the test query."""
        return factories.GradingInfo.create_batch(3)


class TestUpsert:
    def test_it_creates_new_record_if_no_matching_exists(
        self, svc, application_instance, pyramid_request
    ):
        lti_params = pyramid_request.lti_params
        result = svc.upsert(
            pyramid_request.lti_user,
            lti_params.get("lis_result_sourcedid"),
            lti_params.get("lis_outcome_service_url"),
        )

        assert result == Any.instance_of(GradingInfo)

        # Check the h_user data are there
        assert result.h_username == pyramid_request.lti_user.h_user.username
        assert result.h_display_name == pyramid_request.lti_user.h_user.display_name

        # Check the LTI user data are there
        assert result.user_id == pyramid_request.lti_user.user_id
        assert result.application_instance == application_instance

        assert result.lis_result_sourcedid == lti_params["lis_result_sourcedid"]
        assert result.lis_outcome_service_url == lti_params["lis_outcome_service_url"]
        assert result.context_id == pyramid_request.lti_user.lti.course_id
        assert result.resource_link_id == pyramid_request.lti_user.lti.assignment_id

    def test_it_updates_existing_record_if_matching_exists(
        self, svc, pyramid_request, lti_user, application_instance
    ):
        grading_info = factories.GradingInfo(
            application_instance=application_instance,
            user_id=lti_user.user_id,
            context_id=pyramid_request.lti_user.lti.course_id,
            resource_link_id=pyramid_request.lti_user.lti.assignment_id,
        )
        pyramid_request.lti_user.display_name = "updated_display_name"

        svc.upsert(
            pyramid_request.lti_user,
            pyramid_request.lti_params.get("lis_result_sourcedid"),
            pyramid_request.lti_params.get("lis_outcome_service_url"),
        )

        assert grading_info.h_display_name == "updated_display_name"

    @pytest.mark.parametrize(
        "param",
        ("lis_result_sourcedid", "lis_outcome_service_url"),
    )
    def test_it_does_nothing_with_required_parameter_missing(
        self, svc, pyramid_request, param
    ):
        del pyramid_request.lti_params[param]

        assert not svc.upsert(
            pyramid_request.lti_user,
            pyramid_request.lti_params.get("lis_result_sourcedid"),
            pyramid_request.lti_params.get("lis_outcome_service_url"),
        )

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        lti_params = {
            "lis_result_sourcedid": "result_sourcedid",
            "lis_outcome_service_url": "https://somewhere.else",
        }
        pyramid_request.lti_user.lti.course_id = "random context"
        pyramid_request.lti_user.lti.assignment_id = "random resource link id"
        pyramid_request.lti_params.update(lti_params)

        return pyramid_request


@pytest.fixture
def svc(pyramid_request):
    context = mock.create_autospec(LTILaunchResource, spec_set=True, instance=True)

    return GradingInfoService(context, pyramid_request)
