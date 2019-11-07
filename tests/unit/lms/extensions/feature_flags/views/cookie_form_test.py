import pytest
from pyramid import httpexceptions

from lms.extensions.feature_flags.views.cookie_form import CookieFormViews


class TestFeatureFlagsCookieFormViews:
    def test_get_passes_the_feature_flags_to_the_template(
        self, pyramid_request, FeatureFlagsCookieHelper, cookie_helper
    ):
        views = CookieFormViews(pyramid_request)

        template_data = views.get()

        FeatureFlagsCookieHelper.assert_called_once_with(pyramid_request)
        cookie_helper.get_all.assert_called_once_with()
        assert template_data["flags"] == cookie_helper.get_all.return_value

    def test_post_sets_cookie_and_redirects_browser(
        self, pyramid_request, FeatureFlagsCookieHelper, cookie_helper
    ):
        returned = CookieFormViews(pyramid_request).post()

        assert returned == Redirect302To("http://example.com/flags")
        FeatureFlagsCookieHelper.assert_called_once_with(pyramid_request)
        cookie_helper.set_cookie.assert_called_once_with(returned)

    def test_post_flashes_success_message(self, pyramid_request):
        CookieFormViews(pyramid_request).post()

        assert pyramid_request.session.peek_flash("feature_flags") == [
            "Feature flags saved in cookie ✔"
        ]

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route("feature_flags_cookie_form", "/flags")


class Redirect302To:
    """Matches any HTTPFound redirect to the given location."""

    def __init__(self, location):
        self.location = location

    def __eq__(self, other):
        return (
            isinstance(other, httpexceptions.HTTPFound)
            and other.location == self.location
        )


@pytest.fixture(autouse=True)
def FeatureFlagsCookieHelper(patch):
    return patch(
        "lms.extensions.feature_flags.views.cookie_form.FeatureFlagsCookieHelper"
    )


@pytest.fixture
def cookie_helper(FeatureFlagsCookieHelper):
    return FeatureFlagsCookieHelper.return_value
