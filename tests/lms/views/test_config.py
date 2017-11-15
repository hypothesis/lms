from lms.views import config_xml


class TestConfigXml(object):
    def test_it_renders_the_config_xml(self, pyramid_request):
        response = config_xml(pyramid_request)
        assert response is not None
