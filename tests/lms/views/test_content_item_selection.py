from urllib.parse import urlparse
from lms.views import content_item_selection


class TestContentItemSelection(object):

    def test_it_redirects_to_oauth_provider(self, lti_launch_request):
        response = content_item_selection(lti_launch_request)

        location = urlparse(response.location)

        assert response.code == 302
        assert location.netloc == 'hypothesis.instructure.com'
