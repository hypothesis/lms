from unittest.mock import create_autospec, sentinel

import pytest

from lms.models import ApplicationInstance
from lms.services.d2l_api.factory import d2l_api_client_factory


def test_d2l_api_client_factory(
    application_instance_service,
    http_service,
    oauth_http_service,
    aes_service,
    pyramid_request,
    BasicClient,
    D2LAPIClient,
    file_service,
    lti_user,
):
    ai = create_autospec(ApplicationInstance)
    application_instance_service.get_current.return_value = ai

    service = d2l_api_client_factory(sentinel.context, pyramid_request)

    ai.settings.get.assert_called_once_with("desire2learn", "client_id")
    ai.settings.get_secret.assert_called_once_with(
        aes_service, "desire2learn", "client_secret"
    )
    BasicClient.assert_called_once_with(
        lms_host=ai.lms_host.return_value,
        client_id=ai.settings.get.return_value,
        client_secret=ai.settings.get_secret.return_value,
        redirect_uri=pyramid_request.route_url("d2l_api.oauth.callback"),
        http_service=http_service,
        oauth_http_service=oauth_http_service,
    )
    D2LAPIClient.assert_called_once_with(
        BasicClient.return_value, file_service=file_service, lti_user=lti_user
    )
    assert service == D2LAPIClient.return_value


@pytest.fixture(autouse=True)
def BasicClient(patch):
    return patch("lms.services.d2l_api.factory.BasicClient")


@pytest.fixture(autouse=True)
def D2LAPIClient(patch):
    return patch("lms.services.d2l_api.factory.D2LAPIClient")
