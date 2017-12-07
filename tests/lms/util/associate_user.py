from pyramid.view import view_config
from lms.util.associate_user import associate_user


#@view_config(route_name='content_item_selection', request_method='POST')
def test_view_function(request):
    return 

class TestAssociateUser(object):

    def test_it_finds_an_existing_user(self, lti_launch_request):
        response = content_item_selection(lti_launch_request)

        location = urlparse(response.location)

        assert response.code == 302
        assert location.netloc == 'hypothesis.instructure.com'

    def test_it_creates_a_user(self, lti_launch_request):
        pass
#        response = content_item_selection(lti_launch_request)
#
#        location = urlparse(response.location)
#
#        assert response.code == 302
#        assert location.netloc == 'hypothesis.instructure.com'
