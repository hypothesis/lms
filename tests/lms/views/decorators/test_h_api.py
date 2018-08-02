# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json
import mock
import pytest

from pyramid.httpexceptions import HTTPBadGateway
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.httpexceptions import HTTPGatewayTimeout
import requests.exceptions

from lms.views.decorators.h_api import create_h_user
from lms.util import MissingToolConsumerIntanceGUIDError
from lms.util import MissingUserIDError


@pytest.mark.usefixtures("post", "util")
class TestCreateHUser:
    def test_it_400s_if_no_oauth_consumer_key_param(self, create_h_user, pyramid_request):
        del pyramid_request.params["oauth_consumer_key"]

        with pytest.raises(HTTPBadRequest, match="oauth_consumer_key"):
            create_h_user(pyramid_request, mock.sentinel.jwt)

    def test_it_continues_to_the_wrapped_func_if_feature_not_enabled(self, create_h_user, pyramid_request, wrapped):
        pyramid_request.params = {"oauth_consumer_key": "foo"}

        returned = create_h_user(pyramid_request, mock.sentinel.jwt)

        wrapped.assert_called_once_with(pyramid_request, mock.sentinel.jwt)
        assert returned == wrapped.return_value

    def test_it_doesnt_use_the_h_api_if_feature_not_enabled(self, create_h_user, post, pyramid_request):
        pyramid_request.params = {"oauth_consumer_key": "foo"}

        create_h_user(pyramid_request, mock.sentinel.jwt)

        assert not post.called

    def test_it_400s_if_generate_username_raises_MissingToolConsumerInstanceGUIDError(self, create_h_user, pyramid_request, util):
        util.generate_username.side_effect = MissingToolConsumerIntanceGUIDError()

        with pytest.raises(HTTPBadRequest, match="tool_consumer_instance_guid"):
            create_h_user(pyramid_request, mock.sentinel.jwt)

    def test_it_400s_if_generate_username_raises_MissingUserIDError(self, create_h_user, pyramid_request, util):
        util.generate_username.side_effect = MissingUserIDError()

        with pytest.raises(HTTPBadRequest, match="user_id"):
            create_h_user(pyramid_request, mock.sentinel.jwt)

    def test_it_400s_if_generate_provider_raises_MissingToolConsumerInstanceGUIDError(self, create_h_user, pyramid_request, util):
        util.generate_provider.side_effect = MissingToolConsumerIntanceGUIDError()

        with pytest.raises(HTTPBadRequest, match="tool_consumer_instance_guid"):
            create_h_user(pyramid_request, mock.sentinel.jwt)

    def test_it_400s_if_generate_provider_unique_id_raises_MissingUserIDError(self, create_h_user, pyramid_request, util):
        util.generate_provider_unique_id.side_effect = MissingUserIDError()

        with pytest.raises(HTTPBadRequest, match="user_id"):
            create_h_user(pyramid_request, mock.sentinel.jwt)

    def test_it_creates_the_user_in_h(self, create_h_user, post, pyramid_request):
        create_h_user(pyramid_request, mock.sentinel.jwt)

        post.assert_called_once_with(
            "https://example.com/api/users",
            auth=("TEST_CLIENT_ID", "TEST_CLIENT_SECRET"),
            data=json.dumps({
                "username": "test_username",
                "display_name": "test_display_name",
                "authority": "TEST_AUTHORITY",
                "identities": [{
                    "provider": "test_provider",
                    "provider_unique_id": "test_provider_unique_id",
                }],
            }),
            timeout=1,
        )

    def test_it_504s_if_the_h_request_times_out(self, create_h_user, patch, post, pyramid_request):
        post.side_effect = requests.exceptions.ReadTimeout()

        with pytest.raises(HTTPGatewayTimeout):
            create_h_user(pyramid_request, mock.sentinel.jwt)

    def test_it_continues_to_the_wrapped_function_if_h_200s(self, create_h_user, pyramid_request, wrapped):
        returned = create_h_user(pyramid_request, mock.sentinel.jwt)

        wrapped.assert_called_once_with(pyramid_request, mock.sentinel.jwt)
        assert returned == wrapped.return_value

    def test_it_continues_to_the_wrapped_function_if_h_409s(self, create_h_user, post, pyramid_request, wrapped):
        post.return_value.status_code = 409

        returned = create_h_user(pyramid_request, mock.sentinel.jwt)

        wrapped.assert_called_once_with(pyramid_request, mock.sentinel.jwt)
        assert returned == wrapped.return_value

    @pytest.mark.parametrize("status", (500, 501, 502, 503, 504, 400, 401, 403, 404, 408))
    def test_it_502s_for_unexpected_errors_from_h(self, create_h_user, post, pyramid_request, status):
        post.return_value.status_code = status

        with pytest.raises(HTTPBadGateway, match="Connecting to Hypothesis failed"):
            create_h_user(pyramid_request, mock.sentinel.jwt)

    @pytest.fixture
    def create_h_user(self, wrapped):
        # Return the actual wrapper function so that tests can call it directly.
        return create_h_user(wrapped)

    @pytest.fixture
    def post(self, patch):
        post = patch("lms.views.decorators.h_api.requests.post")
        post.return_value = mock.create_autospec(
            requests.models.Response,
            instance=True,
            status_code=200,
        )
        return post

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params = {
            # A valid oauth_consumer_key (matches one for which the
            # provisioning features are enabled).
            "oauth_consumer_key": "Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef",
        }
        return pyramid_request

    @pytest.fixture
    def util(self, patch):
        util = patch("lms.views.decorators.h_api.util")
        util.generate_username.return_value = "test_username"
        util.generate_display_name.return_value = "test_display_name"
        util.generate_provider.return_value = "test_provider"
        util.generate_provider_unique_id.return_value = "test_provider_unique_id"
        return util

    @pytest.fixture
    def wrapped(self):
        """Return the wrapped view function."""
        return mock.MagicMock()
