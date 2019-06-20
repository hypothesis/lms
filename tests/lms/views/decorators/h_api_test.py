from unittest import mock
import pytest

from pyramid.httpexceptions import HTTPBadRequest, HTTPInternalServerError

from requests import Response

from lms.services import HAPIError
from lms.services import HAPINotFoundError
from lms.views.decorators import h_api
from lms.services.hapi import HypothesisAPIService
from lms.resources import LTILaunchResource
from lms.values import LTIUser


@pytest.mark.usefixtures("hapi_svc")
class TestUpsertHUser:
    def test_it_invokes_patch_for_user_update(
        self, upsert_h_user, context, pyramid_request, hapi_svc
    ):

        upsert_h_user(context, pyramid_request)

        hapi_svc.patch.assert_called_once_with(
            "users/test_username", {"display_name": "test_display_name"}
        )

    def test_it_raises_if_patch_raises_unexpected_error(
        self, upsert_h_user, context, pyramid_request, hapi_svc
    ):
        hapi_svc.patch.side_effect = HAPIError("whatever")

        with pytest.raises(HTTPInternalServerError, match="whatever"):
            upsert_h_user(context, pyramid_request)

    def test_it_raises_if_post_raises(
        self, upsert_h_user, context, pyramid_request, hapi_svc
    ):
        # It will only invoke POST if PATCH raises HAPINotFoundError
        hapi_svc.patch.side_effect = HAPINotFoundError("whatever")
        hapi_svc.post.side_effect = HAPIError("Oops")

        with pytest.raises(HTTPInternalServerError, match="Oops"):
            upsert_h_user(context, pyramid_request)

    def test_it_continues_to_the_wrapped_func_if_feature_not_enabled(
        self, upsert_h_user, context, pyramid_request, wrapped
    ):
        context.provisioning_enabled = False

        returned = upsert_h_user(context, pyramid_request)

        wrapped.assert_called_once_with(context, pyramid_request)
        assert returned == wrapped.return_value

    def test_it_doesnt_use_the_h_api_if_feature_not_enabled(
        self, upsert_h_user, context, hapi_svc, pyramid_request
    ):
        context.provisioning_enabled = False

        upsert_h_user(context, pyramid_request)

        hapi_svc.post.assert_not_called()

    def test_it_raises_if_h_username_raises(
        self, upsert_h_user, context, pyramid_request
    ):
        type(context).h_username = mock.PropertyMock(side_effect=HTTPBadRequest("Oops"))

        with pytest.raises(HTTPBadRequest, match="Oops"):
            upsert_h_user(context, pyramid_request)

    def test_it_raises_if_h_provider_raises(
        self, upsert_h_user, context, pyramid_request
    ):
        type(context).h_provider = mock.PropertyMock(side_effect=HTTPBadRequest("Oops"))

        with pytest.raises(HTTPBadRequest, match="Oops"):
            upsert_h_user(context, pyramid_request)

    def test_it_raises_if_provider_unique_id_raises(
        self, upsert_h_user, context, pyramid_request
    ):
        type(context).h_provider_unique_id = mock.PropertyMock(
            side_effect=HTTPBadRequest("Oops")
        )

        with pytest.raises(HTTPBadRequest, match="Oops"):
            upsert_h_user(context, pyramid_request)

    def test_it_creates_the_user_in_h_if_it_does_not_exist(
        self, upsert_h_user, context, hapi_svc, pyramid_request
    ):
        hapi_svc.patch.side_effect = HAPINotFoundError("whatever")

        upsert_h_user(context, pyramid_request)

        hapi_svc.post.assert_called_once_with(
            "users",
            {
                "username": "test_username",
                "display_name": "test_display_name",
                "authority": "TEST_AUTHORITY",
                "identities": [
                    {
                        "provider": "test_provider",
                        "provider_unique_id": "test_provider_unique_id",
                    }
                ],
            },
        )

    def test_it_continues_to_the_wrapped_function(
        self, upsert_h_user, context, pyramid_request, wrapped
    ):
        returned = upsert_h_user(context, pyramid_request)

        wrapped.assert_called_once_with(context, pyramid_request)
        assert returned == wrapped.return_value

    @pytest.fixture
    def upsert_h_user(self, wrapped):
        # Return the actual wrapper function so that tests can call it directly.
        return h_api.upsert_h_user(wrapped)


@pytest.mark.usefixtures("hapi_svc")
class TestUpsertCourseGroup:
    def test_it_does_nothing_if_the_feature_isnt_enabled(
        self, upsert_course_group, context, pyramid_request, wrapped, hapi_svc
    ):
        # If the auto provisioning feature isn't enabled for this application
        # instance then upsert_course_group() doesn't do anything - just calls the
        # wrapped view.
        context.provisioning_enabled = False

        returned = upsert_course_group(context, pyramid_request)

        hapi_svc.patch.assert_not_called()
        hapi_svc.put.assert_not_called()
        wrapped.assert_called_once_with(context, pyramid_request)
        assert returned == wrapped.return_value

    def test_it_calls_the_group_update_api(
        self, upsert_course_group, context, pyramid_request, hapi_svc
    ):
        upsert_course_group(context, pyramid_request)

        hapi_svc.patch.assert_called_once_with(
            "groups/test_groupid", {"name": "test_group_name"}
        )

    def test_it_raises_if_updating_the_group_fails(
        self, upsert_course_group, context, pyramid_request, hapi_svc
    ):
        # If the group update API call fails for any non-404 reason then the
        # view raises an exception and an error page is shown.
        hapi_svc.patch.side_effect = HAPIError("Oops")

        with pytest.raises(HTTPInternalServerError, match="Oops"):
            upsert_course_group(context, pyramid_request)

    def test_if_the_group_doesnt_exist_it_creates_it(
        self, upsert_course_group, context, pyramid_request, hapi_svc
    ):
        pyramid_request.lti_user = LTIUser(
            user_id="TEST_USER_ID",
            oauth_consumer_key="TEST_OAUTH_CONSUMER_KEY",
            roles="instructor",
        )
        hapi_svc.patch.side_effect = HAPINotFoundError()

        upsert_course_group(context, pyramid_request)

        hapi_svc.put.assert_called_once_with(
            "groups/test_groupid",
            {"groupid": "test_groupid", "name": "test_group_name"},
            "acct:test_username@TEST_AUTHORITY",
        )

    def test_it_raises_if_creating_the_group_fails(
        self, upsert_course_group, context, pyramid_request, hapi_svc
    ):
        pyramid_request.lti_user = LTIUser(
            user_id="TEST_USER_ID",
            oauth_consumer_key="TEST_OAUTH_CONSUMER_KEY",
            roles="instructor",
        )
        hapi_svc.patch.side_effect = HAPINotFoundError()
        hapi_svc.put.side_effect = HAPIError("Oops")

        with pytest.raises(HTTPInternalServerError, match="Oops"):
            upsert_course_group(context, pyramid_request)

    def test_if_the_group_doesnt_exist_and_the_user_isnt_allowed_to_create_groups_it_400s(
        self, upsert_course_group, context, pyramid_request, hapi_svc
    ):
        pyramid_request.lti_user = LTIUser(
            user_id="TEST_USER_ID",
            oauth_consumer_key="TEST_OAUTH_CONSUMER_KEY",
            roles="learner",
        )
        hapi_svc.patch.side_effect = HAPINotFoundError()

        with pytest.raises(
            HTTPBadRequest, match="Instructor must launch assignment first"
        ):
            upsert_course_group(context, pyramid_request)

        hapi_svc.put.assert_not_called()

    def test_it_calls_and_returns_the_wrapped_view(
        self, upsert_course_group, context, pyramid_request, wrapped
    ):
        returned = upsert_course_group(context, pyramid_request)

        wrapped.assert_called_once_with(context, pyramid_request)
        assert returned == wrapped.return_value

    @pytest.fixture
    def upsert_course_group(self, wrapped):
        # Return the actual wrapper function so that tests can call it directly.
        return h_api.upsert_course_group(wrapped)


@pytest.mark.usefixtures("hapi_svc")
class TestAddUserToGroup:
    def test_it_doesnt_post_to_the_api_if_feature_not_enabled(
        self, add_user_to_group, context, pyramid_request, hapi_svc
    ):
        context.provisioning_enabled = False

        add_user_to_group(context, pyramid_request)

        hapi_svc.post.assert_not_called()

    def test_it_continues_to_the_wrapped_func_if_feature_not_enabled(
        self, add_user_to_group, context, pyramid_request, wrapped
    ):
        context.provisioning_enabled = False

        returned = add_user_to_group(context, pyramid_request)

        wrapped.assert_called_once_with(context, pyramid_request)
        assert returned == wrapped.return_value

    def test_it_adds_the_user_to_the_group(
        self, add_user_to_group, context, pyramid_request, hapi_svc
    ):
        add_user_to_group(context, pyramid_request)

        hapi_svc.post.assert_called_once_with(
            "groups/test_groupid/members/acct:test_username@TEST_AUTHORITY"
        )

    def test_it_raises_if_post_raises(
        self, add_user_to_group, context, pyramid_request, hapi_svc
    ):
        hapi_svc.post.side_effect = HAPIError("Oops")

        with pytest.raises(HTTPInternalServerError, match="Oops"):
            add_user_to_group(context, pyramid_request)

    def test_it_continues_to_the_wrapped_func(
        self, add_user_to_group, context, pyramid_request, wrapped
    ):
        returned = add_user_to_group(context, pyramid_request)

        wrapped.assert_called_once_with(context, pyramid_request)
        assert returned == wrapped.return_value

    @pytest.fixture
    def add_user_to_group(self, wrapped):
        # Return the actual wrapper function so that tests can call it directly.
        return h_api.add_user_to_group(wrapped)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params[
            "tool_consumer_instance_guid"
        ] = "test_tool_consumer_instance_guid"
        pyramid_request.params["context_id"] = "test_context_id"
        return pyramid_request


@pytest.fixture
def context():
    context = mock.create_autospec(
        LTILaunchResource,
        spec_set=True,
        instance=True,
        h_display_name="test_display_name",
        h_groupid="test_groupid",
        h_group_name="test_group_name",
        h_username="test_username",
        h_userid="acct:test_username@TEST_AUTHORITY",
        h_provider="test_provider",
        h_provider_unique_id="test_provider_unique_id",
        provisioning_enabled=True,
    )
    return context


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.params.update(
        {
            "oauth_consumer_key": "Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef",
            "tool_consumer_instance_guid": "TEST_GUID",
            "context_id": "TEST_CONTEXT",
        }
    )
    pyramid_request.db = mock.MagicMock()
    return pyramid_request


@pytest.fixture
def wrapped():
    """Return the wrapped view function."""
    return mock.MagicMock()


@pytest.fixture
def hapi_svc(patch, pyramid_config):
    hapi_svc = mock.create_autospec(HypothesisAPIService, spec_set=True, instance=True)
    hapi_svc.patch.return_value = mock.create_autospec(
        Response, instance=True, status_code=200, reason="OK", text=""
    )
    hapi_svc.post.return_value = mock.create_autospec(
        Response, instance=True, status_code=200, reason="OK", text=""
    )
    pyramid_config.register_service(hapi_svc, name="hapi")
    return hapi_svc
