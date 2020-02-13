from urllib.parse import urlencode

import pytest
from h_matchers import Any

from lms.views.helpers import via_url


class TestViaURL:
    DEFAULT_OPTIONS = {
        "via.open_sidebar": "1",
        # This is the `request.host_url`
        "via.request_config_from_frame": "http://example.com",
        "via.config_frame_ancestor_level": "2",
    }

    @pytest.mark.parametrize(
        "params,expected_extras",
        (
            ({}, None),
            ({"extra": "value"}, "extra=value"),
            ({"a": ["v1", "v2"]}, "a=v1&a=v2"),
            (
                # If the document URL already has via.open_sidebar or
                # via.request_config_from_frame query params it replaces them with
                # its own values.
                {
                    "extra": "value",
                    "via.open_sidebar": "IGNORED1",
                    "via.request_config_from_frame": "IGNORED2",
                },
                "extra=value",
            ),
        ),
    )
    def test_it_merges_params_correctly(self, pyramid_request, params, expected_extras):
        final_url = via_url(
            pyramid_request, f"http://doc.example.com/?{urlencode(params, doseq=True)}"
        )

        assert final_url == Any.url.containing_query(self.DEFAULT_OPTIONS)

        if expected_extras:
            assert final_url == Any.url.containing_query(expected_extras)

    @pytest.mark.parametrize(
        "url", ("http://doc.example.com", "https://doc.example.com",)
    )
    def test_it_passes_through_the_url(self, pyramid_request, url):
        final_url = via_url(pyramid_request, url)

        assert final_url == Any.url.with_host("test_via_server.is").with_path(url)

    @pytest.mark.usefixtures("via3_feature_flag")
    def test_it_returns_via3_url_if_feature_flag_is_set(self, pyramid_request):
        url = "http://example.com"

        final_url = via_url(pyramid_request, url)

        assert final_url == Any.url.with_host("test_via3_server.is").with_query(
            dict(self.DEFAULT_OPTIONS, url=url)
        )

    @pytest.fixture
    def via3_feature_flag(self, pyramid_request):
        pyramid_request.feature = lambda feature: feature == "use_via3_url"
