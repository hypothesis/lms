from lti.views import create_application_instance
from lti.models import ApplicationInstance


class TestApplicationInstance(object):
    def test_it_creates_an_application_instance(self, pyramid_request):
        pyramid_request.method = 'POST'
        pyramid_request.params = {
            'lms_url': 'canvas.example.com',
            'email': 'email@example.com',
        }
        create_application_instance(pyramid_request)
        assert pyramid_request.db.query(ApplicationInstance).filter(
            ApplicationInstance.lms_url == pyramid_request.params['lms_url']).count() == 1
