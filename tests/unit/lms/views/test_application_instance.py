import pytest

from lms.views.application_instances import (
    create_application_instance,
    new_application_instance,
)
from tests.conftest import TEST_SETTINGS


@pytest.mark.usefixtures("application_instance_service")
class TestCreateApplicationInstance:
    def test_it_creates_an_application_instance(
        self, pyramid_request, application_instance_service
    ):
        ai_data = create_application_instance(pyramid_request)

        application_instance_service.create.assert_called_once_with(
            pyramid_request.params["lms_url"],
            pyramid_request.params["email"],
            pyramid_request.params["developer_key"],
            pyramid_request.params["developer_secret"],
            TEST_SETTINGS["aes_secret"],
        )
        assert (
            ai_data["consumer_key"]
            == application_instance_service.create.return_value.consumer_key
        )
        assert (
            ai_data["shared_secret"]
            == application_instance_service.create.return_value.shared_secret
        )

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.method = "POST"
        pyramid_request.params = {
            "lms_url": "canvas.example.com",
            "email": "email@example.com",
            "developer_key": "",
            "developer_secret": "",
        }
        return pyramid_request


class TestNewApplicationInstance:
    def test_it(self, pyramid_request):
        assert new_application_instance(pyramid_request) == {}
