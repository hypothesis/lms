import pytest

from lms.resources import CanvasOAuth2RedirectResource


class TestCanvasOAuth2RedirectResource:
    def test_does_not_set_jsconfig_if_no_exception(self, pyramid_request):
        resource = CanvasOAuth2RedirectResource(pyramid_request)
        assert resource.js_config is None

    def test_sets_jsconfig_if_exception(self, pyramid_request, JSConfig):
        resource = CanvasOAuth2RedirectResource(pyramid_request)

        # Simulate exception happening during request processing.
        pyramid_request.exception = Exception("Oh no")

        # Accessing `resource.js_config` afterwards should initialize the config.
        js_config = resource.js_config

        JSConfig.assert_called_once_with(resource, pyramid_request)
        assert js_config == JSConfig.return_value
        assert resource.js_config == js_config


@pytest.fixture
def JSConfig(patch):
    return patch("lms.resources.canvas_oauth2_redirect.JSConfig")


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.exception = None
    return pyramid_request
