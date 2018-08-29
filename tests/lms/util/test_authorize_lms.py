from urllib.parse import urlparse, parse_qs
import json
from pyramid.response import Response
from lms.util import authorize_lms, save_token
from lms.models import build_from_lms_url
from lms.models import User
from lms.models import find_by_state


@authorize_lms(
    authorization_base_endpoint='login/oauth2/auth',
    redirect_endpoint='canvas_oauth_callback'
)
def view_function(_request, **_):
    return Response("<h1>Howdy</h1>")


@authorize_lms(
    authorization_base_endpoint='login/oauth2/auth',
    redirect_endpoint='canvas_oauth_callback',
    oauth_condition=lambda request: False
)
def oauth_condition_view_function(_request, **_):
    return Response("<h1>Howdy</h1>")


def build_save_token_view(assertions):
    @save_token
    def save_token_view_function(request, **kwargs):
        assertions(request, **kwargs)
        return Response("<h1>Howdy</h1>")
    return save_token_view_function


def create_application_instance(lti_launch_request):
    lms_url = "https://example.com"
    email = "example@example.com"
    session = lti_launch_request.db
    application_instance = build_from_lms_url(lms_url, email, 'test', b'test',
                                              encryption_key=lti_launch_request.
                                              registry.settings['aes_secret'])
    session.add(application_instance)
    session.flush()
    return application_instance


def create_user(lti_launch_request):
    user_id = lti_launch_request.params['user_id']
    existing_user = User(lms_guid=user_id)

    db_session = lti_launch_request.db
    db_session.add(existing_user)
    db_session.flush()
    return existing_user


class TestAuthorizeLms:
    """Test the associate user decorator."""

    def test_it_redirects_for_oauth(self, lti_launch_request):
        create_application_instance(lti_launch_request)
        user = create_user(lti_launch_request)

        response = view_function(lti_launch_request, user=user)
        assert response.code == 302
        assert "https://hypothesis.instructure.com/login/oauth2/auth" in response.location

    def test_it_saves_state(self, lti_launch_request):
        create_application_instance(lti_launch_request)
        user = create_user(lti_launch_request)

        response = view_function(lti_launch_request, user=user)
        query_params = parse_qs(urlparse(response.location).query)

        oauth_state = find_by_state(lti_launch_request.db, query_params['state'][0])

        expected_lti_params = json.dumps(dict(lti_launch_request.params))

        assert oauth_state.lti_params != ""
        assert oauth_state.lti_params is not None
        assert oauth_state.lti_params == expected_lti_params

    def test_it_only_redirects_if_condition_is_truthy(self, lti_launch_request):
        create_application_instance(lti_launch_request)
        user = create_user(lti_launch_request)

        response = oauth_condition_view_function(lti_launch_request, user=user)
        assert response.status_code == 200
        assert response.body == b'<h1>Howdy</h1>'

    def test_it_saves_token(self, oauth_response):
        def assertions(_request, **kwargs):
            user = kwargs['user']
            token = kwargs['token']
            assert user.id is not None
            assert user.id == token.user_id
        response = build_save_token_view(assertions)(oauth_response)
        assert response.status_code == 200
