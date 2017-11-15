from lms.views import content_item_selection


class TestContentItemSelection(object):
    def test_it_provides_the_return_url_to_the_template(self, lti_launch_request):
        response = content_item_selection(lti_launch_request)
        params = lti_launch_request.params
        assert response['content_item_return_url'] == params['content_item_return_url']
