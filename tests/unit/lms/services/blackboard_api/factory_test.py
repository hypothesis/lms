from unittest.mock import sentinel

import pytest

from lms.services.blackboard_api.factory import blackboard_api_client_factory


def test_blackboard_api_client_factory(
    application_instance_service,
    http_service,
    oauth_http_service,
    oauth2_token_service,
    pyramid_request,
    BasicClient,
    BlackboardAPIClient,
):
    application_instance = application_instance_service.get.return_value
    settings = pyramid_request.registry.settings

    service = blackboard_api_client_factory(sentinel.context, pyramid_request)

    BasicClient.assert_called_once_with(
        blackboard_host=application_instance.lms_host(),
        client_id=settings["blackboard_api_client_id"],
        client_secret=settings["blackboard_api_client_secret"],
        redirect_uri=pyramid_request.route_url("blackboard_api.oauth.callback"),
        http_service=http_service,
        oauth_http_service=oauth_http_service,
        oauth2_token_service=oauth2_token_service,
    )
    BlackboardAPIClient.assert_called_once_with(BasicClient.return_value)
    assert service == BlackboardAPIClient.return_value


@pytest.fixture(autouse=True)
def BasicClient(patch):
    return patch("lms.services.blackboard_api.factory.BasicClient")


@pytest.fixture(autouse=True)
def BlackboardAPIClient(patch):
    return patch("lms.services.blackboard_api.factory.BlackboardAPIClient")
