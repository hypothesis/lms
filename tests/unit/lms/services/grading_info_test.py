from unittest import mock

import pytest
from h_matchers import Any

from lms.models import GradingInfo
from lms.resources import LTILaunchResource
from lms.services.grading_info import GradingInfoService
from lms.values import HUser, LTIUser


class TestGetByAssignment:
    def test_it_retrieves_matching_records(
        self, svc, lti_params, grading_info, another_grading_info, lti_user,
    ):

        grading_infos = svc.get_by_assignment(
            oauth_consumer_key=lti_user.oauth_consumer_key,
            context_id=lti_params["context_id"],
            resource_link_id=lti_params["resource_link_id"],
        )

        assert len(grading_infos) == 2

    def test_it_returns_empty_list_if_no_matching_records(
        self, svc, lti_params, lti_user
    ):
        grading_infos = svc.get_by_assignment(
            oauth_consumer_key=lti_user.oauth_consumer_key,
            context_id=lti_params["context_id"],
            resource_link_id=lti_params["resource_link_id"],
        )

        assert not grading_infos

    @pytest.fixture
    def another_grading_info(self, lti_params, db_session):
        another_grading_info = GradingInfo(**lti_params)

        add_users(
            another_grading_info,
            h_user=HUser(
                authority="TEST_AUTHORITY",
                username="teststudent",
                display_name="Another Test",
            ),
            lti_user=LTIUser("TEST_USER_ID_2", "TEST_OAUTH_CONSUMER_KEY", "TEST_ROLES"),
        )

        db_session.add(another_grading_info)
        return another_grading_info


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
        self,
        svc,
        pyramid_request,
        h_user,
        lti_user,
        grading_info,
        db_session,
        lti_params,
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
    return LTIUser("TEST_USER_ID", "TEST_OAUTH_CONSUMER_KEY", "TEST_ROLES")


@pytest.fixture
def h_user():
    return HUser(
        authority="TEST_AUTHORITY", username="seanh", display_name="Sample Student"
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


def add_users(grading_info, h_user, lti_user):
    grading_info.h_username = h_user.username
    grading_info.h_display_name = h_user.display_name

    grading_info.oauth_consumer_key = lti_user.oauth_consumer_key
    grading_info.user_id = lti_user.user_id


@pytest.fixture
def grading_info(lti_params, h_user, lti_user, db_session):
    grading_info = GradingInfo(**lti_params)

    add_users(grading_info, h_user, lti_user)

    db_session.add(grading_info)
    return grading_info
