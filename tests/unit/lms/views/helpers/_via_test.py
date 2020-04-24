from urllib.parse import urlencode

import pytest
from h_matchers import Any

from lms.views.helpers import via_url


class TestViaURL:
    DEFAULT_OPTIONS = {
        "via.client.openSidebar": "1",
        # This is the `request.host_url`
        "via.client.requestConfigFromFrame.origin": "http://example.com",
        "via.client.requestConfigFromFrame.ancestorLevel": "2",
    }

    def test_if_creates_the_correct_via_url(self, pyramid_request):
        url = "http://example.com"

        final_url = via_url(pyramid_request, url)

        assert final_url == Any.url.matching(
            "http://test_via3_server.is/route"
        ).with_query(dict(self.DEFAULT_OPTIONS, url=url))

    @pytest.mark.usefixtures("legacy_via_feature_flag")
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
                    "via.client.openSidebar": "IGNORED1",
                    "via.client.requestConfigFromFrame.origin": "IGNORED2",
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

    @pytest.mark.usefixtures("legacy_via_feature_flag")
    @pytest.mark.parametrize(
        "url", ("http://doc.example.com", "https://doc.example.com",)
    )
    def test_it_passes_through_the_url(self, pyramid_request, url):
        final_url = via_url(pyramid_request, url)

        assert final_url == Any.url.with_host("test_legacy_via_server.is").with_path(
            url
        )

    @pytest.fixture
    def legacy_via_feature_flag(self, pyramid_request):
        pyramid_request.feature = lambda feature: feature == "use_legacy_via"
