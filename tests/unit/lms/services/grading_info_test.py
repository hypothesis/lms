from unittest import mock

import pytest
from h_matchers import Any

from lms.models import GradingInfo, HUser, LTIUser
from lms.resources import LTILaunchResource
from lms.services.grading_info import GradingInfoService


class TestGetByAssignment:
    def test_it(self, svc, matching_grading_infos):
        grading_infos = svc.get_by_assignment(
            "matching_oauth_consumer_key",
            "matching_context_id",
            "matching_resource_link_id",
        )

        assert list(grading_infos) == matching_grading_infos

    @pytest.mark.parametrize(
        "oauth_consumer_key,context_id,resource_link_id",
        [
            (
                "other_oauth_consumer_key",
                "matching_context_id",
                "matching_resource_link_id",
            ),
            (
                "matching_oauth_consumer_key",
                "other_context_id",
                "matching_resource_link_id",
            ),
            (
                "matching_oauth_consumer_key",
                "matching_context_id",
                "other_resource_link_id",
            ),
            ("other_oauth_consumer_key", "other_context_id", "other_resource_link_id"),
        ],
    )
    def test_it_returns_an_empty_list_if_there_are_no_matching_GradingInfos(
        self, svc, oauth_consumer_key, context_id, resource_link_id
    ):
        grading_infos = svc.get_by_assignment(
            oauth_consumer_key, context_id, resource_link_id
        )

        assert list(grading_infos) == []

    @pytest.fixture(autouse=True)
    def matching_grading_infos(self, db_session):
        """Add some GradingInfo's that should match the DB query in the test above."""
        matching_grading_infos = [self.grading_info("matching", i) for i in range(3)]
        db_session.add_all(matching_grading_infos)
        return matching_grading_infos

    @pytest.fixture(autouse=True)
    def noise_grading_infos(self, db_session):
        """Add some GradingInfo's that should *not* match the test query."""
        noise_grading_infos = [self.grading_info("noise", i) for i in range(3)]
        db_session.add_all(noise_grading_infos)
        return noise_grading_infos

    def grading_info(self, prefix, index):
        return GradingInfo(
            lis_result_sourcedid=f"{prefix}_lis_result_sourcedid_{index}",
            lis_outcome_service_url=f"{prefix}_lis_outcomes_service_url_{index}",
            oauth_consumer_key=f"{prefix}_oauth_consumer_key",
            user_id=f"{prefix}_user_id_{index}",
            context_id=f"{prefix}_context_id",
            resource_link_id=f"{prefix}_resource_link_id",
            tool_consumer_info_product_family_code=f"{prefix}_tool_consumer_info_product_family_code_{index}",
            h_username=f"{prefix}_h_username_{index}",
            h_display_name=f"{prefix}_h_display_name_{index}",
        )


class TestUpsertFromRequest:
    def test_it_creates_new_record_if_no_matching_exists(
        self, svc, pyramid_request, h_user, lti_user, db_session, lti_params
    ):
        svc.upsert_from_request(pyramid_request, h_user, lti_user)

        result = db_session.get_last_inserted()
        assert result == Any.instance_of(GradingInfo)

        # Check the lti_params are there
        assert self.model_as_dict(result) == Any.dict.containing(lti_params)

        # Check the h_user data are there
        assert result.h_username == h_user.username
        assert result.h_display_name == h_user.display_name

        # Check the LTI user data are there
        assert result.oauth_consumer_key == lti_user.oauth_consumer_key
        assert result.user_id == lti_user.user_id

    def test_it_updates_existing_record_if_matching_exists(
        self, svc, pyramid_request, h_user, lti_user, db_session,
    ):
        # Update a couple of attributes on the model...
        h_user = h_user._replace(display_name="Someone Else")

        pyramid_request.POST["lis_result_sourcedid"] = "something different"

        svc.upsert_from_request(pyramid_request, h_user, lti_user)

        result = db_session.get_last_inserted()
        assert result == Any.instance_of(GradingInfo)
        assert result.lis_result_sourcedid == "something different"
        assert result.h_display_name == "Someone Else"

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
        self, svc, pyramid_request, h_user, lti_user, db_session, param
    ):
        del pyramid_request.POST[param]

        svc.upsert_from_request(pyramid_request, h_user, lti_user)

        assert db_session.get_last_inserted() is None

    @pytest.mark.parametrize("param", ("tool_consumer_info_product_family_code",))
    def test_it_works_fine_with_optional_parameter_missing(
        self, svc, pyramid_request, h_user, lti_user, db_session, param
    ):
        del pyramid_request.POST[param]

        svc.upsert_from_request(pyramid_request, h_user, lti_user)
        assert db_session.get_last_inserted() == Any.instance_of(GradingInfo)

    @classmethod
    def model_as_dict(cls, model):
        return {col.key: getattr(model, col.key) for col in model.iter_columns()}

    @pytest.fixture
    def db_session(self, db_session):
        db_session.get_last_inserted = lambda: db_session.query(
            GradingInfo
        ).one_or_none()
        return db_session

    @pytest.fixture
    def pyramid_request(self, pyramid_request, lti_params):
        pyramid_request.POST.update(lti_params)

        return pyramid_request


@pytest.fixture
def lti_user():
    return LTIUser("test_user_id", "matching_oauth_consumer_key", "test_roles")


@pytest.fixture
def h_user():
    return HUser(
        authority="test_authority", username="seanh", display_name="Sample Student"
    )


@pytest.fixture
def svc(pyramid_request):
    context = mock.create_autospec(
        LTILaunchResource, spec_set=True, instance=True, h_user=h_user
    )

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
