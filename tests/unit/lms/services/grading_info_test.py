from operator import attrgetter
from unittest import mock

import pytest
from h_matchers import Any

from lms.models import GradingInfo
from lms.resources import LTILaunchResource
from lms.services.grading_info import GradingInfoService
from tests import factories

pytestmark = pytest.mark.usefixtures("application_instance_service")


class TestGetByAssignment:
    def test_it(self, svc, matching_grading_infos, application_instance):
        grading_infos = svc.get_by_assignment(
            application_instance,
            "matching_context_id",
            "matching_resource_link_id",
        )

        assert sorted(grading_infos, key=attrgetter("id")) == sorted(
            matching_grading_infos, key=attrgetter("id")
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
        grading_infos = svc.get_by_assignment(
            application_instance if filter_application_instance else None,
            context_id,
            resource_link_id,
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


class TestUpsertFromRequest:
    def test_it_creates_new_record_if_no_matching_exists(
        self, svc, application_instance, pyramid_request, lti_params
    ):
        result = svc.upsert_from_request(pyramid_request)

        assert result == Any.instance_of(GradingInfo)

        # Check the lti_params are there
        assert self.model_as_dict(result) == Any.dict.containing(lti_params)

        # Check the h_user data are there
        assert result.h_username == pyramid_request.lti_user.h_user.username
        assert result.h_display_name == pyramid_request.lti_user.h_user.display_name

        # Check the LTI user data are there
        assert result.user_id == pyramid_request.lti_user.user_id
        assert result.application_instance_id == application_instance.id

    def test_it_updates_existing_record_if_matching_exists(
        self, svc, pyramid_request, lti_user, application_instance
    ):
        grading_info = factories.GradingInfo(
            application_instance=application_instance,
            user_id=lti_user.user_id,
            context_id=pyramid_request.params["context_id"],
            resource_link_id=pyramid_request.params["resource_link_id"],
        )
        pyramid_request.lti_user = pyramid_request.lti_user._replace(
            display_name="updated_display_name"
        )

        svc.upsert_from_request(pyramid_request)

        assert grading_info.h_display_name == "updated_display_name"

    @pytest.mark.parametrize(
        "param",
        (
            "lis_result_sourcedid",
            "lis_outcome_service_url",
            "context_id",
            "resource_link_id",
        ),
    )
    def test_it_does_nothing_with_required_parameter_missing(
        self, svc, pyramid_request, param
    ):
        del pyramid_request.POST[param]

        assert not svc.upsert_from_request(pyramid_request)

    @pytest.mark.parametrize("param", ("tool_consumer_info_product_family_code",))
    def test_it_works_fine_with_optional_parameter_missing(
        self, svc, pyramid_request, param
    ):
        del pyramid_request.POST[param]

        assert svc.upsert_from_request(pyramid_request) == Any.instance_of(GradingInfo)

    @classmethod
    def model_as_dict(cls, model):
        return {col: getattr(model, col) for col in model.columns()}

    @pytest.fixture
    def pyramid_request(self, pyramid_request, lti_params):
        pyramid_request.POST.update(lti_params)

        return pyramid_request


@pytest.fixture
def svc(pyramid_request):
    context = mock.create_autospec(LTILaunchResource, spec_set=True, instance=True)

    return GradingInfoService(context, pyramid_request)


@pytest.fixture
def lti_params():
    return {
        "lis_result_sourcedid": "result_sourcedid",
        "lis_outcome_service_url": "https://somewhere.else",
        "context_id": "random context",
        "resource_link_id": "random resource link id",
        "tool_consumer_info_product_family_code": "MyFakeLTITool",
    }
