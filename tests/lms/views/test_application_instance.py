from lms.views import create_application_instance
from lms.models import ApplicationInstance


class TestApplicationInstance(object):
    def test_it_creates_an_application_instance(self, pyramid_request):
        pyramid_request.method = 'POST'
        pyramid_request.params = {
            'lms_url': 'canvas.example.com',
            'email': 'email@example.com',
            'developer_key': '',
            'developer_secret': ''
        }
        initial_count = pyramid_request.db.query(ApplicationInstance).filter(
            ApplicationInstance.lms_url == pyramid_request.params['lms_url']).count()
        create_application_instance(pyramid_request)
        new_count = pyramid_request.db.query(ApplicationInstance).filter(
            ApplicationInstance.lms_url == pyramid_request.params['lms_url']).count()
        assert new_count == initial_count + 1
