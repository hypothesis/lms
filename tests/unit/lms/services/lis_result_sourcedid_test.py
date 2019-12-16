from unittest import mock

import pytest
from h_matchers import Any

from lms.models import LISResultSourcedId
from lms.resources import LTILaunchResource
from lms.services.lis_result_sourcedid import LISResultSourcedIdService
from lms.values import HUser, LTIUser


class TestFetchStudentsByAssignment:
    def test_it_retrieves_matching_records(
        self,
        svc,
        lti_params,
        lis_result_sourcedid,
        another_lis_result_sourcedid,
        lti_user,
    ):

        students = svc.fetch_students_by_assignment(
            oauth_consumer_key=lti_user.oauth_consumer_key,
            context_id=lti_params["context_id"],
            resource_link_id=lti_params["resource_link_id"],
        )

        assert len(students) == 2

    def test_it_returns_empty_list_if_no_matching_records(
        self, svc, lti_params, lti_user
    ):
        students = svc.fetch_students_by_assignment(
            oauth_consumer_key=lti_user.oauth_consumer_key,
            context_id=lti_params["context_id"],
            resource_link_id=lti_params["resource_link_id"],
        )

        assert not students

    @pytest.fixture
    def another_lis_result_sourcedid(self, lti_params, db_session):
        another_lis_result_sourcedid = LISResultSourcedId(**lti_params)

        add_users(
            another_lis_result_sourcedid,
            h_user=HUser(
                authority="TEST_AUTHORITY",
                username="teststudent",
                display_name="Another Test",
            ),
            lti_user=LTIUser("TEST_USER_ID_2", "TEST_OAUTH_CONSUMER_KEY", "TEST_ROLES"),
        )

        db_session.add(another_lis_result_sourcedid)
        return another_lis_result_sourcedid


class TestUpsertFromRequest:
    def test_it_creates_new_record_if_no_matching_exists(
        self, svc, pyramid_request, h_user, lti_user, db_session, lti_params
    ):
        svc.upsert_from_request(pyramid_request, h_user, lti_user)

        result = db_session.get_last_inserted()
        assert result == Any.instance_of(LISResultSourcedId)

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
        lis_result_sourcedid,
        db_session,
        lti_params,
    ):
        # Update a couple of attributes on the model...
        h_user = h_user._replace(display_name="Someone Else")

        pyramid_request.POST["lis_result_sourcedid"] = "something different"

        svc.upsert_from_request(pyramid_request, h_user, lti_user)

        result = db_session.get_last_inserted()
        assert result == Any.instance_of(LISResultSourcedId)
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
        assert db_session.get_last_inserted() == Any.instance_of(LISResultSourcedId)

    @classmethod
    def model_as_dict(cls, model):
        return {col.key: getattr(model, col.key) for col in model.iter_columns()}

    @pytest.fixture
    def db_session(self, db_session):
        db_session.get_last_inserted = lambda: db_session.query(
            LISResultSourcedId
        ).one_or_none()
        return db_session

    @pytest.fixture
    def pyramid_request(self, pyramid_request, lti_params):
        pyramid_request.POST.update(lti_params)

        return pyramid_request


class TestAssignmentIsGradable:
    def test_it_returns_False_if_not_gradable(self, svc, pyramid_request):
        result = svc.is_assignment_gradable(pyramid_request)

        assert result is False

    def test_it_returns_True_if_assignment_is_gradable(
        self, svc, pyramid_request, lti_params
    ):
        pyramid_request.POST.update(lti_params)

        result = svc.is_assignment_gradable(pyramid_request)

        assert result is True


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

    return LISResultSourcedIdService(context, pyramid_request)


@pytest.fixture
def lti_params():
    return {
        "lis_result_sourcedid": "result_sourcedid",
        "lis_outcome_service_url": "https://somewhere.else",
        "context_id": "random context",
        "resource_link_id": "random resource link id",
        "tool_consumer_info_product_family_code": "MyFakeLTITool",
    }


def add_users(lis_result_sourcedid, h_user, lti_user):
    lis_result_sourcedid.h_username = h_user.username
    lis_result_sourcedid.h_display_name = h_user.display_name

    lis_result_sourcedid.oauth_consumer_key = lti_user.oauth_consumer_key
    lis_result_sourcedid.user_id = lti_user.user_id


@pytest.fixture
def lis_result_sourcedid(lti_params, h_user, lti_user, db_session):
    lis_result_sourcedid = LISResultSourcedId(**lti_params)

    add_users(lis_result_sourcedid, h_user, lti_user)

    db_session.add(lis_result_sourcedid)
    return lis_result_sourcedid
