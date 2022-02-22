import pytest

from lms.views.api.refresh import get_refreshed_token

pytestmark = pytest.mark.usefixtures("canvas_api_client", "oauth2_token_service")


def test_get_refreshed_token(pyramid_request, canvas_api_client, oauth2_token_service):
    get_refreshed_token(pyramid_request)

    canvas_api_client.get_refreshed_token.assert_called_once_with(
        oauth2_token_service.get.return_value.refresh_token
    )
