import pytest
from h_matchers import Any

from lms.views.application_instances import (
    create_application_instance,
    new_application_instance,
)


class TestCreateApplicationInstance:
    @pytest.mark.parametrize(
        "developer_key,canvas_sections_enabled, canvas_groups_enabled",
        [("test_developer_key", False, True), ("", False, False)],
    )
    def test_it(
        self,
        pyramid_request,
        application_instance_service,
        developer_key,
        canvas_sections_enabled,
        canvas_groups_enabled,
    ):
        pyramid_request.params["developer_key"] = developer_key
        pyramid_request.params["developer_secret"] = "test_developer_secret"

        result = create_application_instance(pyramid_request)

        application_instance_service.create.assert_called_once_with(
            "canvas.example.com",
            "email@example.com",
            developer_key,
            "test_developer_secret",
            settings=Any.dict.containing(
                {
                    "canvas": {
                        "sections_enabled": canvas_sections_enabled,
                        "groups_enabled": canvas_groups_enabled,
                    }
                }
            ),
        )
        assert result == {
            "consumer_key": application_instance_service.create.return_value.consumer_key,
            "shared_secret": application_instance_service.create.return_value.shared_secret,
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
