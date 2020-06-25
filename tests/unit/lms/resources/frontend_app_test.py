import pytest

from lms.resources import FrontendAppResource


class TestFrontendAppResource:
    def test_it(self, pyramid_request, JSConfig):
        resource = FrontendAppResource(pyramid_request)

        config = resource.js_config

        JSConfig.assert_called_once_with(resource, pyramid_request)
        assert config == JSConfig.return_value


@pytest.fixture
def JSConfig(patch):
    return patch("lms.resources.frontend_app.JSConfig")
