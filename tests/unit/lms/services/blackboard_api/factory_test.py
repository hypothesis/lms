from unittest.mock import sentinel

import pytest

from lms.services.blackboard_api.factory import blackboard_api_client_factory

pytestmark = pytest.mark.usefixtures("basic_blackboard_api_client")


def test_blackboard_api_client_factory(
    pyramid_request, BlackboardAPIClient, basic_blackboard_api_client
):
    client = blackboard_api_client_factory(sentinel.context, pyramid_request)

    BlackboardAPIClient.assert_called_once_with(basic_blackboard_api_client)
    assert client == BlackboardAPIClient.return_value


@pytest.fixture(autouse=True)
def BlackboardAPIClient(patch):
    return patch("lms.services.blackboard_api.factory.BlackboardAPIClient")
