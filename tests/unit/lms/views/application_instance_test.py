import pytest

from lms.views.application_instances import (
    create_application_instance,
    new_application_instance,
)


class TestCreateApplicationInstance:
    def test_it(self, pyramid_request, application_instance_service):
        pyramid_request.params["developer_key"] = "  DEVELOPER_KEY  "
        pyramid_request.params["developer_secret"] = " DEVELOPER_SECRET "

        result = create_application_instance(pyramid_request)

        application_instance_service.create_application_instance.assert_called_once_with(
            lms_url="canvas.example.com",
            email="email@example.com",
            developer_key="DEVELOPER_KEY",
            developer_secret="DEVELOPER_SECRET",
        )
        created_ai = (
            application_instance_service.create_application_instance.return_value
        )
        assert result == {
            "consumer_key": created_ai.consumer_key,
            "shared_secret": created_ai.shared_secret,
        }

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
        assert not new_application_instance(pyramid_request)
