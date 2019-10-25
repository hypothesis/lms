import pytest

from lms.views.helpers import via_url


class TestViaURL:
    @pytest.mark.parametrize(
        "document_url,expected_via_url",
        [
            # If the document URL has no query params it adds the Via query
            # params.
            (
                "https://example.com",
                "http://TEST_VIA_SERVER.is/https://example.com"
                "?via.open_sidebar=1"
                "&via.request_config_from_frame=http%3A%2F%2Fexample.com",
            ),
            (
                "http://example.com",
                "http://TEST_VIA_SERVER.is/http://example.com"
                "?via.open_sidebar=1"
                "&via.request_config_from_frame=http%3A%2F%2Fexample.com",
            ),
            # If the document URL already has query params it appends the Via
            # params and preserves the existing ones.
            (
                "http://example.com?foo=FOO&bar=BAR",
                "http://TEST_VIA_SERVER.is/http://example.com"
                "?foo=FOO&bar=BAR&via.open_sidebar=1"
                "&via.request_config_from_frame=http%3A%2F%2Fexample.com",
            ),
            # If the document URL already has via.open_sidebar or
            # via.request_config_from_frame query params it replaces them with
            # its own values.
            (
                "http://example.com?thing=blah&via.open_sidebar=FOO&via.request_config_from_frame=BAR",
                "http://TEST_VIA_SERVER.is/http://example.com"
                "?thing=blah&via.open_sidebar=1"
                "&via.request_config_from_frame=http%3A%2F%2Fexample.com",
            ),
        ],
    )
    def test_it_returns_the_url_with_query_params(
        self, pyramid_request, document_url, expected_via_url
    ):
        # A valid oauth_consumer_key (matches one for which the provisioning
        # features are enabled).
        # fmt: off
        pyramid_request.params["oauth_consumer_key"] = "Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef"
        # fmt: on
        assert via_url(pyramid_request, document_url) == expected_via_url

    def test_it_returns_via2_url_if_use_via2_service_feature_flag_is_set(
        self, pyramid_request
    ):
        pyramid_request.feature = lambda feature: feature == "use_via2_service"

        assert via_url(pyramid_request, "http://example.com").startswith(
            "http://TEST_VIA2_SERVER.is/"
        )
