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
        "via.external_link_mode": "new-tab",
    }

    def test_if_creates_the_correct_via_url(self, pyramid_request):
        url = "http://example.com"

        final_url = via_url(pyramid_request, url)

        assert final_url == Any.url.matching(
            "http://test_via3_server.is/route"
        ).with_query(dict(self.DEFAULT_OPTIONS, url=url))

    pywb_test_params = pytest.mark.parametrize(
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

    @pytest.mark.usefixtures("legacy_via_feature_flag")
    @pywb_test_params
    def test_it_merges_params_correctly_for_legacy_via(
        self, pyramid_request, params, expected_extras
    ):
        final_url = via_url(
            pyramid_request, f"http://doc.example.com/?{urlencode(params, doseq=True)}"
        )

        assert final_url == Any.url.with_host("test_legacy_via_server.is")
        assert final_url == Any.url.with_path("/http://doc.example.com/")
        assert final_url == Any.url.containing_query(self.DEFAULT_OPTIONS)

        if expected_extras:
            assert final_url == Any.url.containing_query(expected_extras)

    def test_it_routes_to_via_for_html(self, pyramid_request):
        final_url = via_url(
            pyramid_request, "http://doc.example.com/", content_type="html"
        )

        assert final_url == Any.url.with_host("test_legacy_via_server.is")
        assert final_url == Any.url.with_path("/http://doc.example.com/")

    @pytest.mark.usefixtures("via_rewriter_feature_flag")
    @pywb_test_params
    def test_it_merges_params_correctly_for_via_rewriter(
        self, pyramid_request, params, expected_extras
    ):
        final_url = via_url(
            pyramid_request,
            f"http://doc.example.com/?{urlencode(params, doseq=True)}",
            content_type="html",
        )

        assert final_url == Any.url.with_host("test_via3_server.is")
        assert final_url == Any.url.with_path("/html/v/http://doc.example.com/")
        assert final_url == Any.url.containing_query(self.DEFAULT_OPTIONS)

        if expected_extras:
            assert final_url == Any.url.containing_query(expected_extras)

    @pytest.mark.usefixtures("via_rewriter_feature_flag")
    def test_it_adds_the_rewriter_option_if_the_flag_is_enabled(self, pyramid_request):
        final_url = via_url(pyramid_request, "http://doc.example.com")

        assert final_url == Any.url.containing_query({"via.rewrite": "1"})

    def test_it_redirects_to_via3_view_pdf_directly_for_google_drive(
        self, pyramid_request
    ):
        google_drive_url = "https://drive.google.com/uc?id=<SOME-ID>&export=download"
        final_url = via_url(pyramid_request, google_drive_url)

        assert final_url == Any.url.matching(
            "http://test_via3_server.is/pdf"
        ).containing_query({"url": google_drive_url})

    def test_it_redirects_to_via3_view_pdf_directly_if_content_type_is_pdf(
        self, pyramid_request
    ):
        final_url = via_url(pyramid_request, "any url", content_type="pdf")

        assert (
            final_url == Any.url.matching("http://test_via3_server.is/pdf").with_query()
        )

    @pytest.mark.usefixtures("legacy_via_feature_flag")
    @pytest.mark.parametrize(
        "url", ("http://doc.example.com", "https://doc.example.com")
    )
    def test_it_passes_through_the_url(self, pyramid_request, url):
        final_url = via_url(pyramid_request, url)

        assert final_url == Any.url.with_host("test_legacy_via_server.is").with_path(
            url
        )

    @pytest.fixture
    def legacy_via_feature_flag(self, pyramid_request):
        pyramid_request.feature = lambda feature: feature == "use_legacy_via"

    @pytest.fixture
    def via_rewriter_feature_flag(self, pyramid_request):
        pyramid_request.feature = lambda feature: feature == "use_via_rewriter"
