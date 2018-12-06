# -*- coding: utf-8 -*-

import json
from unittest import mock
import pytest

from pyramid.httpexceptions import HTTPBadRequest

from requests import ConnectionError
from requests import HTTPError
from requests import ReadTimeout
from requests import Response
from requests import TooManyRedirects

from lms.services import HAPIError
from lms.services import HAPINotFoundError
from lms.views.decorators import h_api
from lms.services.hapi import HypothesisAPIService
from lms.config.resources import LTILaunch


@pytest.mark.usefixtures("hapi_svc")
class TestCreateHUser:
    def test_it_raises_if_post_raises(
        self, create_h_user, context, pyramid_request, hapi_svc
    ):
        hapi_svc.post.side_effect = HAPIError("Oops")

        with pytest.raises(HAPIError, match="Oops"):
            create_h_user(pyramid_request, mock.sentinel.jwt, context)

    def test_it_continues_to_the_wrapped_func_if_feature_not_enabled(
        self, create_h_user, context, pyramid_request, wrapped
    ):
        pyramid_request.params["oauth_consumer_key"] = "foo"

        returned = create_h_user(pyramid_request, mock.sentinel.jwt, context)

        wrapped.assert_called_once_with(pyramid_request, mock.sentinel.jwt)
        assert returned == wrapped.return_value

    def test_it_doesnt_use_the_h_api_if_feature_not_enabled(
        self, create_h_user, context, hapi_svc, pyramid_request
    ):
        pyramid_request.params["oauth_consumer_key"] = "foo"

        create_h_user(pyramid_request, mock.sentinel.jwt, context)

        hapi_svc.post.assert_not_called()

    def test_it_raises_if_h_username_raises(
        self, create_h_user, context, pyramid_request
    ):
        type(context).h_username = mock.PropertyMock(side_effect=HTTPBadRequest("Oops"))

        with pytest.raises(HTTPBadRequest, match="Oops"):
            create_h_user(pyramid_request, mock.sentinel.jwt, context)

    def test_it_raises_if_h_provider_raises(
        self, create_h_user, context, pyramid_request
    ):
        type(context).h_provider = mock.PropertyMock(side_effect=HTTPBadRequest("Oops"))

        with pytest.raises(HTTPBadRequest, match="Oops"):
            create_h_user(pyramid_request, mock.sentinel.jwt, context)

    def test_it_raises_if_provider_unique_id_raises(
        self, create_h_user, context, pyramid_request
    ):
        type(context).h_provider_unique_id = mock.PropertyMock(
            side_effect=HTTPBadRequest("Oops")
        )

        with pytest.raises(HTTPBadRequest, match="Oops"):
            create_h_user(pyramid_request, mock.sentinel.jwt, context)

    def test_it_creates_the_user_in_h(
        self, create_h_user, context, hapi_svc, pyramid_request
    ):
        create_h_user(pyramid_request, mock.sentinel.jwt, context)

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
            statuses=[409],
        )

    def test_it_continues_to_the_wrapped_function(
        self, create_h_user, context, pyramid_request, wrapped
    ):
        returned = create_h_user(pyramid_request, mock.sentinel.jwt, context)

        wrapped.assert_called_once_with(pyramid_request, mock.sentinel.jwt)
        assert returned == wrapped.return_value

    @pytest.fixture
    def create_h_user(self, wrapped):
        # Return the actual wrapper function so that tests can call it directly.
        return h_api.create_h_user(wrapped)


@pytest.mark.usefixtures("hapi_svc")
class TestCreateCourseGroup:
    def test_it_does_nothing_if_the_feature_isnt_enabled(
        self, create_course_group, context, pyramid_request, wrapped, hapi_svc
    ):
        # If the auto provisioning feature isn't enabled for this application
        # instance then create_course_group() doesn't do anything - just calls the
        # wrapped view.
        pyramid_request.params["oauth_consumer_key"] = "foo"

        returned = create_course_group(pyramid_request, mock.sentinel.jwt, context)

        hapi_svc.patch.assert_not_called()
        hapi_svc.put.assert_not_called()
        wrapped.assert_called_once_with(pyramid_request, mock.sentinel.jwt)
        assert returned == wrapped.return_value

    def test_it_400s_if_roles_param_missing(
        self, create_course_group, context, pyramid_request
    ):
        del pyramid_request.params["roles"]

        with pytest.raises(HTTPBadRequest, match="roles"):
            create_course_group(pyramid_request, mock.sentinel.jwt, context)

    def test_it_calls_the_group_update_api(
        self, create_course_group, context, pyramid_request, hapi_svc
    ):
        create_course_group(pyramid_request, mock.sentinel.jwt, context)

        hapi_svc.patch.assert_called_once_with(
            "groups/test_groupid", {"name": "test_group_name"}
        )

    def test_it_raises_if_updating_the_group_fails(
        self, create_course_group, context, pyramid_request, hapi_svc
    ):
        # If the group update API call fails for any non-404 reason then the
        # view raises an exception and an error page is shown.
        hapi_svc.patch.side_effect = HAPIError("Oops")

        with pytest.raises(HAPIError, match="Oops"):
            create_course_group(pyramid_request, mock.sentinel.jwt, context)

    def test_if_the_group_doesnt_exist_it_creates_it(
        self, create_course_group, context, pyramid_request, hapi_svc
    ):
        hapi_svc.patch.side_effect = HAPINotFoundError()

        create_course_group(pyramid_request, mock.sentinel.jwt, context)

        hapi_svc.put.assert_called_once_with(
            "groups/test_groupid",
            {"groupid": "test_groupid", "name": "test_group_name"},
            "acct:test_username@TEST_AUTHORITY",
        )

    def test_if_the_group_doesnt_exist_and_the_user_isnt_allowed_to_create_groups_it_400s(
        self, create_course_group, context, pyramid_request, hapi_svc
    ):
        hapi_svc.patch.side_effect = HAPINotFoundError()
        pyramid_request.params["roles"] = "Learner"

        with pytest.raises(
            HTTPBadRequest, match="Instructor must launch assignment first"
        ):
            create_course_group(pyramid_request, mock.sentinel.jwt, context)

        hapi_svc.put.assert_not_called()

    def test_it_calls_and_returns_the_wrapped_view(
        self, create_course_group, context, pyramid_request, wrapped
    ):
        returned = create_course_group(pyramid_request, mock.sentinel.jwt, context)

        wrapped.assert_called_once_with(pyramid_request, mock.sentinel.jwt)
        assert returned == wrapped.return_value

    @pytest.fixture
    def create_course_group(self, wrapped):
        # Return the actual wrapper function so that tests can call it directly.
        return h_api.create_course_group(wrapped)


@pytest.mark.usefixtures("hapi_svc")
class TestAddUserToGroup:
    def test_it_doesnt_post_to_the_api_if_feature_not_enabled(
        self, add_user_to_group, context, pyramid_request, hapi_svc
    ):
        pyramid_request.params["oauth_consumer_key"] = "foo"

        add_user_to_group(pyramid_request, mock.sentinel.jwt, context)

        hapi_svc.post.assert_not_called()

    def test_it_continues_to_the_wrapped_func_if_feature_not_enabled(
        self, add_user_to_group, context, pyramid_request, wrapped
    ):
        pyramid_request.params["oauth_consumer_key"] = "foo"

        returned = add_user_to_group(pyramid_request, mock.sentinel.jwt, context)

        wrapped.assert_called_once_with(pyramid_request, mock.sentinel.jwt)
        assert returned == wrapped.return_value

    def test_it_adds_the_user_to_the_group(
        self, add_user_to_group, context, pyramid_request, hapi_svc
    ):
        add_user_to_group(pyramid_request, mock.sentinel.jwt, context)

        hapi_svc.post.assert_called_once_with(
            "groups/test_groupid/members/acct:test_username@TEST_AUTHORITY"
        )

    def test_it_raises_if_post_raises(
        self, add_user_to_group, context, pyramid_request, hapi_svc
    ):
        hapi_svc.post.side_effect = HAPIError("Oops")

        with pytest.raises(HAPIError, match="Oops"):
            add_user_to_group(pyramid_request, mock.sentinel.jwt, context)

    def test_it_continues_to_the_wrapped_func(
        self, add_user_to_group, context, pyramid_request, wrapped
    ):
        returned = add_user_to_group(pyramid_request, mock.sentinel.jwt, context)

        wrapped.assert_called_once_with(pyramid_request, mock.sentinel.jwt)
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
        LTILaunch,
        spec_set=True,
        instance=True,
        h_display_name="test_display_name",
        h_groupid="test_groupid",
        h_group_name="test_group_name",
        h_username="test_username",
        h_userid="acct:test_username@TEST_AUTHORITY",
        h_provider="test_provider",
        h_provider_unique_id="test_provider_unique_id",
    )
    return context


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.params.update(
        {
            # A valid oauth_consumer_key (matches one for which the
            # provisioning features are enabled).
            "oauth_consumer_key": "Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef",
            "tool_consumer_instance_guid": "TEST_GUID",
            "context_id": "TEST_CONTEXT",
            "roles": "Instructor,urn:lti:instrole:ims/lis/Administrator",
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
    hapi_svc.post.return_value = mock.create_autospec(
        Response, instance=True, status_code=200, reason="OK", text=""
    )
    pyramid_config.register_service(hapi_svc, name="hapi")
    return hapi_svc
