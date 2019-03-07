from urllib.parse import urlparse, parse_qs
import json

import pytest
from pyramid.response import Response

from lms.util import authorize_lms, save_token
from lms.models import User, find_lti_params


@authorize_lms(
    authorization_base_endpoint="login/oauth2/auth",
    redirect_endpoint="canvas_oauth_callback",
)
def view_function(_request, **_):
    return Response("<h1>Howdy</h1>")


@authorize_lms(
    authorization_base_endpoint="login/oauth2/auth",
    redirect_endpoint="canvas_oauth_callback",
    oauth_condition=lambda request: False,
)
def oauth_condition_view_function(_request, **_):
    return Response("<h1>Howdy</h1>")


def build_save_token_view(assertions):
    @save_token
    def save_token_view_function(request, **kwargs):
        assertions(request, **kwargs)
        return Response("<h1>Howdy</h1>")

    return save_token_view_function


def create_user(lti_launch_request):
    user_id = lti_launch_request.params["user_id"]
    existing_user = User(lms_guid=user_id)

    db_session = lti_launch_request.db
    db_session.add(existing_user)
    db_session.flush()
    return existing_user


class TestAuthorizeLms:
    """Test the associate user decorator."""

    def test_it_redirects_for_oauth(self, lti_launch_request):
        user = create_user(lti_launch_request)

        response = view_function(lti_launch_request, user=user)
        assert response.code == 302
        assert "https://example.com/login/oauth2/auth" in response.location

    def test_it_saves_lti_params(self, lti_launch_request):
        user = create_user(lti_launch_request)

        response = view_function(lti_launch_request, user=user)
        query_params = parse_qs(urlparse(response.location).query)

        lti_params = find_lti_params(lti_launch_request.db, query_params["state"][0])
        assert lti_params == lti_launch_request.params

    def test_it_only_redirects_if_condition_is_truthy(self, lti_launch_request):
        user = create_user(lti_launch_request)

        response = oauth_condition_view_function(lti_launch_request, user=user)
        assert response.status_code == 200
        assert response.body == b"<h1>Howdy</h1>"

    def test_it_saves_token(self, oauth_response):
        def assertions(_request, **kwargs):
            user = kwargs["user"]
            token = kwargs["token"]
            assert user.id is not None
            assert user.id == token.user_id

        response = build_save_token_view(assertions)(oauth_response)
        assert response.status_code == 200
