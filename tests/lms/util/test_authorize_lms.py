from pyramid.response import Response
from lms.util.authorize_lms import authorize_lms
from lms.models.users import User


def build_mock_view(assertions):
    """Build a mock view function decorated by associate_user"""
    @authorize_lms(
        authorization_base_endpoint='login/oauth2/auth',
        redirect_endpoint='canvas_oauth_callback'
    )
    def test_view_function(request, user):
        assertions(request, user)
        return Response("<h1>Howdy</h1>")

    return test_view_function


class TestAuthorizeLms(object):
    """Test the associate user decorator"""
#    def test_it_redirects_for_oauth(self, lti_launch_request, **kwargs):
#        user_id = lti_launch_request.params['user_id']
#        existing_user = User(lms_guid=user_id)
#
#        db_session = lti_launch_request.db
#        db_session.add(existing_user)
#        db_session.flush()
#
#        def assertions(_request, user):
#            assert user.id == existing_user.id
#        build_mock_view(assertions)(lti_launch_request)
#
#    def test_it_creates_a_user(self, lti_launch_request):
#
#    def test_it_saves_state():


