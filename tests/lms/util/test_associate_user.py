from pyramid.response import Response
from lms.util.associate_user import associate_user
from lms.models.users import User


def build_mock_view(assertions):
    """Build a mock view function decorated by associate_user."""
    @associate_user
    def test_view_function(request, user):
        assertions(request, user)
        return Response("<h1>Howdy</h1>")

    return test_view_function


class TestAssociateUser(object):
    """Test the associate user decorator"""
    def test_it_finds_an_existing_user(self, lti_launch_request, **kwargs):
        user_id = lti_launch_request.params['user_id']
        existing_user = User(lms_guid=user_id)

        db_session = lti_launch_request.db
        db_session.add(existing_user)
        db_session.flush()

        def assertions(_request, user):
            assert user.id == existing_user.id
        build_mock_view(assertions)(lti_launch_request)

    def test_it_creates_a_user(self, lti_launch_request):
        def assertions(request, user):
            request.db.flush()
            assert user.id is not None
        build_mock_view(assertions)(lti_launch_request)

