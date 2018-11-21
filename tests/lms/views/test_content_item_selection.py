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
    @pytest.mark.parametrize(
        "param", ["lti_version", "oauth_version", "oauth_nonce", "oauth_signature"]
    )
    def test_it_raises_if_a_required_launch_param_is_missing(
        self, lti_launch_request, param
    ):
        del lti_launch_request.params[param]

        with pytest.raises(MissingLTIContentItemParamError, match=param):
            content_item_form(
                lti_launch_request,
                lti_params=lti_launch_request.params,
                lms_url="test_lms_url",
                content_item_return_url="content_item_return_url",
            )
