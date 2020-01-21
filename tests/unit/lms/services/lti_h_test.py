from unittest import mock

import pytest
from pyramid.httpexceptions import HTTPBadRequest, HTTPInternalServerError

from lms.models import GroupInfo
from lms.services import HAPIError, HAPINotFoundError
from lms.services.group_info import GroupInfoService
from lms.services.h_api import HAPI
from lms.services.lti_h import LTIHService
from lms.values import HUser, LTIUser


class TestUpsertCourseGroup:
    def test_it_does_nothing_if_the_feature_isnt_enabled(
        self, context, pyramid_request, h_api, lti_h_svc
    ):
        # If the auto provisioning feature isn't enabled for this application
        # instance then upsert_course_group() doesn't do anything - just calls the
        # wrapped view.
        context.provisioning_enabled = False

        lti_h_svc.upsert_course_group()

        h_api.update_group.assert_not_called()

    def test_it_calls_the_group_update_api(
        self, context, pyramid_request, h_api, lti_h_svc
    ):
        lti_h_svc.upsert_course_group()

        h_api.update_group.assert_called_once_with(
            group_id="test_groupid", group_name="test_group_name",
        )
        h_api.create_group.assert_not_called()

    def test_it_raises_if_updating_the_group_fails(
        self, context, pyramid_request, h_api, lti_h_svc
    ):
        # If the group update API call fails for any non-404 reason then the
        # view raises an exception and an error page is shown.
        h_api.update_group.side_effect = HAPIError("Oops")

        with pytest.raises(HTTPInternalServerError, match="Oops"):
            lti_h_svc.upsert_course_group()

    def test_it_creates_the_group_if_it_doesnt_exist(
        self, context, pyramid_request, h_api, lti_h_svc, h_user
    ):
        pyramid_request.lti_user = LTIUser(
            user_id="TEST_USER_ID",
            oauth_consumer_key="TEST_OAUTH_CONSUMER_KEY",
            roles="instructor",
        )
        h_api.update_group.side_effect = HAPINotFoundError()

        lti_h_svc.upsert_course_group()

        h_api.create_group.assert_called_once_with(
            group_id="test_groupid", group_name="test_group_name", creator=h_user,
        )

    def test_it_raises_if_creating_the_group_fails(
        self, context, pyramid_request, h_api, lti_h_svc
    ):
        pyramid_request.lti_user = LTIUser(
            user_id="TEST_USER_ID",
            oauth_consumer_key="TEST_OAUTH_CONSUMER_KEY",
            roles="instructor",
        )
        h_api.update_group.side_effect = HAPINotFoundError()
        h_api.create_group.side_effect = HAPIError("Oops")

        with pytest.raises(HTTPInternalServerError, match="Oops"):
            lti_h_svc.upsert_course_group()

    def test_it_400s_with_missing_group_and_unpriviledged_user(
        self, context, pyramid_request, h_api, lti_h_svc
    ):
        pyramid_request.lti_user = LTIUser(
            user_id="TEST_USER_ID",
            oauth_consumer_key="TEST_OAUTH_CONSUMER_KEY",
            roles="learner",
        )
        h_api.update_group.side_effect = HAPINotFoundError()

        with pytest.raises(
            HTTPBadRequest, match="Instructor must launch assignment first"
        ):
            lti_h_svc.upsert_course_group()

        h_api.create_group.assert_not_called()

    def test_it_upserts_the_GroupInfo_into_the_db(
        self, params, group_info_svc, context, pyramid_request, lti_h_svc
    ):
        lti_h_svc.upsert_course_group()

        group_info_svc.upsert.assert_called_once_with(
            authority_provided_id=context.h_authority_provided_id,
            consumer_key="TEST_OAUTH_CONSUMER_KEY",
            params=params,
        )

    def test_it_doesnt_upsert_GroupInfo_into_the_db_if_creating_the_group_fails(
        self, group_info_svc, context, pyramid_request, h_api, lti_h_svc
    ):
        h_api.update_group.side_effect = HAPINotFoundError()
        h_api.create_group.side_effect = HAPIError("Oops")

        try:
            lti_h_svc.upsert_course_group()
        except:
            pass

        group_info_svc.assert_not_called()

    @pytest.fixture
    def params(self):
        return {
            field.key: f"TEST_{field.key.upper()}" for field in GroupInfo.iter_columns()
        }

    @pytest.fixture
    def pyramid_request(self, params, pyramid_request):
        pyramid_request.params = params
        return pyramid_request


class TestUpsertHUser:
    def test_it_calls_h_api_for_user_update(
        self, context, pyramid_request, h_api, lti_h_svc, h_user
    ):
        lti_h_svc.upsert_h_user()

        h_api.upsert_user.assert_called_once_with(
            h_user=h_user,
            provider="test_provider",
            provider_unique_id="test_provider_unique_id",
        )

    def test_it_raises_if_upsert_user_raises_unexpected_error(
        self, context, pyramid_request, h_api, lti_h_svc
    ):
        h_api.upsert_user.side_effect = HAPIError("whatever")

        with pytest.raises(HTTPInternalServerError, match="whatever"):
            lti_h_svc.upsert_h_user()

    def test_it_doesnt_use_the_h_api_if_feature_not_enabled(
        self, context, h_api, pyramid_request, lti_h_svc
    ):
        context.provisioning_enabled = False

        lti_h_svc.upsert_h_user()

        h_api.upsert_user.assert_not_called()

    def test_it_raises_if_h_user_raises(self, context, pyramid_request, lti_h_svc):
        type(context).h_user = mock.PropertyMock(side_effect=HTTPBadRequest("Oops"))

        with pytest.raises(HTTPBadRequest, match="Oops"):
            lti_h_svc.upsert_h_user()

    def test_it_raises_if_h_provider_raises(self, context, pyramid_request, lti_h_svc):
        type(context).h_provider = mock.PropertyMock(side_effect=HTTPBadRequest("Oops"))

        with pytest.raises(HTTPBadRequest, match="Oops"):
            lti_h_svc.upsert_h_user()

    def test_it_raises_if_provider_unique_id_raises(
        self, context, pyramid_request, lti_h_svc
    ):
        type(context).h_provider_unique_id = mock.PropertyMock(
            side_effect=HTTPBadRequest("Oops")
        )

        with pytest.raises(HTTPBadRequest, match="Oops"):
            lti_h_svc.upsert_h_user()


class TestAddUserToGroups:
    def test_it_doesnt_post_to_the_api_if_feature_not_enabled(
        self, context, pyramid_request, h_api, lti_h_svc
    ):
        context.provisioning_enabled = False

        lti_h_svc.add_user_to_groups()

        h_api.add_user_to_groups.assert_not_called()

    def test_it_adds_the_user_to_the_group(
        self, context, pyramid_request, h_api, lti_h_svc, h_user
    ):
        lti_h_svc.add_user_to_groups()

        h_api.add_user_to_groups.assert_called_once_with(
            h_user=h_user, group_id="test_groupid"
        )

    def test_it_raises_if_post_raises(self, context, pyramid_request, h_api, lti_h_svc):
        h_api.add_user_to_groups.side_effect = HAPIError("Oops")

        with pytest.raises(HTTPInternalServerError, match="Oops"):
            lti_h_svc.add_user_to_groups()

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params[
            "tool_consumer_instance_guid"
        ] = "test_tool_consumer_instance_guid"
        pyramid_request.params["context_id"] = "test_context_id"
        return pyramid_request


@pytest.fixture
def lti_h_svc(pyramid_request):
    return LTIHService(None, pyramid_request)


@pytest.fixture
def h_user():
    return HUser(
        authority="TEST_AUTHORITY",
        username="test_username",
        display_name="test_display_name",
    )


@pytest.fixture
def context(h_user):
    class TestContext:
        h_groupids = ["test_groupid"]
        h_group_name = "test_group_name"
        h_provider = "test_provider"
        h_provider_unique_id = "test_provider_unique_id"
        provisioning_enabled = True
        h_authority_provided_id = "test_authority_provided_id"

    context = TestContext()
    context.h_user = h_user
    return context


@pytest.fixture
def pyramid_request(context, pyramid_request):
    pyramid_request.context = context
    return pyramid_request


@pytest.fixture(autouse=True)
def h_api(patch, pyramid_config):
    h_api = mock.create_autospec(HAPI, spec_set=True, instance=True)

    pyramid_config.register_service(h_api, name="h_api")
    return h_api


@pytest.fixture(autouse=True)
def group_info_svc(pyramid_config):
    group_info_svc = mock.create_autospec(
        GroupInfoService, instance=True, spec_set=True
    )
    pyramid_config.register_service(group_info_svc, name="group_info")
    return group_info_svc
