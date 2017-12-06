from lms.views import content_item_selection
from urllib.parse import urlparse


class TestContentItemSelection(object):
#    def test_it_provides_the_return_url_to_the_template(self, lti_launch_request):
#        response = content_item_selection(lti_launch_request)
#
#        params = lti_launch_request.params
#        assert params['content_item_return_url'] in response.body.decode()

    def test_it_redirects_to_oauth_provider(self, lti_launch_request):
        response = content_item_selection(lti_launch_request)
        import pdb; pdb.set_trace()

        location = urlparse(response.location)

        assert response.code == 302
        assert location.netloc == "atomicjolt.instructure.com"
