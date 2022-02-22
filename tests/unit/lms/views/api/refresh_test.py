import pytest

from lms.views.api.refresh import get_refreshed_token
from tests import factories


@pytest.mark.usefixtures("oauth2_token_service")
def test_get_refreshed_token_with_Canvas(
    pyramid_request,
    application_instance_service,
    canvas_api_client,
    oauth2_token_service,
):
    application_instance_service.get_current.return_value = (
        factories.ApplicationInstance(tool_consumer_info_product_family_code="canvas")
    )

    get_refreshed_token(pyramid_request)

    canvas_api_client.get_refreshed_token.assert_called_once_with(
        oauth2_token_service.get.return_value.refresh_token
    )


def test_get_refreshed_token_with_Blackboard(
    pyramid_request, application_instance_service, blackboard_api_client
):
    application_instance_service.get_current.return_value = (
        factories.ApplicationInstance(
            tool_consumer_info_product_family_code="BlackboardLearn"
        )
    )

    get_refreshed_token(pyramid_request)

    blackboard_api_client.refresh_access_token.assert_called_once_with()
