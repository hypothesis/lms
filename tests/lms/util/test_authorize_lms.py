from urllib.parse import urlparse, parse_qs
from pyramid.response import Response
from lms.util.authorize_lms import authorize_lms
from lms.models.users import User
from lms.models.application_instance import build_from_lms_url
from lms.models.oauth_state import find_by_state
import json


@authorize_lms(
    authorization_base_endpoint='login/oauth2/auth',
    redirect_endpoint='canvas_oauth_callback'
)
def view_function(request, user):
    return Response("<h1>Howdy</h1>")


def create_application_instance(lti_launch_request):
    lms_url = "https://example.com"
    email = "example@example.com"
    session = lti_launch_request.db
    application_instance = build_from_lms_url(lms_url, email)
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



class TestAuthorizeLms(object):
    """Test the associate user decorator"""
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

#    def test_it_throws(): TODO test errors are corectly thrown when values ore
#    not retrieved or saved



