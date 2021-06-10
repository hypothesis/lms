import pytest
from h_matchers import Any

from lms.views.helpers import via_url


class TestViaURL:
    DEFAULT_OPTIONS = {
        # Default options set by h_vialib
        "via.client.ignoreOtherConfiguration": "1",
        "via.client.openSidebar": "1",
        "via.external_link_mode": "new-tab",
        # This is the `request.host_url`
        "via.client.requestConfigFromFrame.origin": "http://example.com",
        "via.client.requestConfigFromFrame.ancestorLevel": "2",
    }

    def test_if_creates_the_correct_via_url(self, pyramid_request):
        url = "http://example.com"

        final_url = via_url(pyramid_request, url)

        url_params = dict(self.DEFAULT_OPTIONS)
        url_params["url"] = url
        url_params["via.sec"] = Any.string()
        url_params["via.blocked_for"] = "lms"
        assert final_url == Any.url.matching(
            "http://test_via_server.is/route"
        ).with_query(url_params)

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

    def test_it_redirects_to_via_view_pdf_directly_for_google_drive(
        self, pyramid_request
    ):
        google_drive_url = "https://drive.google.com/uc?id=<SOME-ID>&export=download"
        final_url = via_url(pyramid_request, google_drive_url)

        assert final_url == Any.url.matching(
            "http://test_via_server.is/pdf"
        ).containing_query({"url": google_drive_url})

    def test_it_redirects_to_via_view_pdf_directly_if_content_type_is_pdf(
        self, pyramid_request
    ):
        final_url = via_url(pyramid_request, "any url", content_type="pdf")

        assert (
            final_url == Any.url.matching("http://test_via_server.is/pdf").with_query()
        )
