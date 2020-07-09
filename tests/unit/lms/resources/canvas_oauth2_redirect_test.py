import pytest

from lms.resources import CanvasOAuth2RedirectResource


class TestCanvasOAuth2RedirectResource:
    def test_sets_jsconfig(self, pyramid_request, JSConfig):
        resource = CanvasOAuth2RedirectResource(pyramid_request)
        JSConfig.assert_called_once_with(resource, pyramid_request)
        assert resource.js_config == JSConfig.return_value


@pytest.fixture
def JSConfig(patch):
    return patch("lms.resources.canvas_oauth2_redirect.JSConfig")
