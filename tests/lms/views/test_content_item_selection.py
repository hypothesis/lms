from unittest.mock import Mock

import pytest

from urllib.parse import urlparse
from lms.exceptions import MissingLTILaunchParamError, MissingLTIContentItemParamError
from lms.views.content_item_selection import content_item_selection, content_item_form
from tests.lms.conftest import unwrap

# The `content_item_selection` view function is wrapped in a series of
# decorators which handle authorization and creating the user/group for the
# current course.
#
# In these tests we only want to test the view function itself, so extract that
# from the decorated function.
content_item_selection = unwrap(content_item_selection)


class TestContentItemSelection:
    # TODO - Tests for `content_item_selection` view
    pass


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
