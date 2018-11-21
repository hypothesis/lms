import pytest

from urllib.parse import urlparse
from lms.exceptions import MissingLTILaunchParamError, MissingLTIContentItemParamError
from lms.views.content_item_selection import content_item_selection, content_item_form


class TestContentItemSelection:
    def test_it_redirects_to_oauth_provider(self, lti_launch_request):
        response = content_item_selection(lti_launch_request)

        location = urlparse(response.location)

        assert response.code == 302
        assert location.netloc == "hypothesis.instructure.com"


class TestContentItemForm:
    def test_raises_for_lti_version_param(self, lti_launch_request):
        del lti_launch_request.params["lti_version"]
        with pytest.raises(
            MissingLTIContentItemParamError,
            match="Required LTI data param for content item selection missing: lti_version",
        ):
            content_item_form(
                lti_launch_request,
                lti_params=lti_launch_request.params,
                lms_url="test_lms_url",
                content_item_return_url="content_item_return_url",
            )

    def test_raises_for_oauth_version_param(self, lti_launch_request):
        del lti_launch_request.params["oauth_version"]
        with pytest.raises(
            MissingLTIContentItemParamError,
            match="Required LTI data param for content item selection missing: oauth_version",
        ):
            content_item_form(
                lti_launch_request,
                lti_params=lti_launch_request.params,
                lms_url="test_lms_url",
                content_item_return_url="content_item_return_url",
            )

    def test_raises_for_oauth_nonce_param(self, lti_launch_request):
        del lti_launch_request.params["oauth_nonce"]
        with pytest.raises(
            MissingLTIContentItemParamError,
            match="Required LTI data param for content item selection missing: oauth_nonce",
        ):
            content_item_form(
                lti_launch_request,
                lti_params=lti_launch_request.params,
                lms_url="test_lms_url",
                content_item_return_url="content_item_return_url",
            )

    def test_raises_for_oauth_signature_param(self, lti_launch_request):
        del lti_launch_request.params["oauth_signature"]
        with pytest.raises(
            MissingLTIContentItemParamError,
            match="Required LTI data param for content item selection missing: oauth_signature",
        ):
            content_item_form(
                lti_launch_request,
                lti_params=lti_launch_request.params,
                lms_url="test_lms_url",
                content_item_return_url="content_item_return_url",
            )
