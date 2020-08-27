import pytest

from lms.resources import OAuth2RedirectResource


class TestOAuth2RedirectResource:
    def test_sets_jsconfig(self, pyramid_request, JSConfig):
        resource = OAuth2RedirectResource(pyramid_request)
        JSConfig.assert_called_once_with(resource, pyramid_request)
        assert resource.js_config == JSConfig.return_value


@pytest.fixture
def JSConfig(patch):
    return patch("lms.resources.oauth2_redirect.JSConfig")
