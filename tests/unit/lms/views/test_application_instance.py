import pytest

from lms.models import ApplicationInstance
from lms.views.application_instances import (
    create_application_instance,
    new_application_instance,
)


class TestCreateApplicationInstance:
    def test_it_creates_an_application_instance(self, pyramid_request):
        create_application_instance(pyramid_request)

        application_instance = pyramid_request.db.query(ApplicationInstance).one()
        assert application_instance.lms_url == "canvas.example.com"
        assert application_instance.requesters_email == "email@example.com"
        assert application_instance.developer_key is None
        assert application_instance.developer_secret is None

    def test_it_saves_the_Canvas_developer_key_and_secret_if_given(
        self, pyramid_request
    ):
        pyramid_request.params["developer_key"] = "example_key"
        pyramid_request.params["developer_secret"] = "example_secret"

        create_application_instance(pyramid_request)

        application_instance = pyramid_request.db.query(ApplicationInstance).one()
        assert application_instance.developer_key == "example_key"
        assert application_instance.developer_secret

    @pytest.mark.parametrize(
        "developer_key,developer_secret",
        [
            # A developer key is given but no secret. Neither should be saved.
            ("example_key", ""),
            # A developer secret is given but no key. Neither should be saved.
            ("", "example_secret"),
        ],
    )
    def test_if_developer_key_or_secret_is_missing_it_doesnt_save_either(
        self, pyramid_request, developer_key, developer_secret
    ):
        pyramid_request.params["developer_key"] = developer_key
        pyramid_request.params["developer_secret"] = developer_secret

        create_application_instance(pyramid_request)

        application_instance = pyramid_request.db.query(ApplicationInstance).one()
        assert application_instance.developer_key is None
        assert application_instance.developer_secret is None

    @pytest.mark.parametrize(
        "developer_key,feature_flag,canvas_sections_enabled",
        [
            ("test_developer_key", True, True),
            ("test_developer_key", False, False),
            ("", True, False),
            ("", False, False),
        ],
    )
    def test_it_sets_canvas_sections_enabled(
        self, pyramid_request, developer_key, feature_flag, canvas_sections_enabled
    ):
        pyramid_request.params["developer_key"] = developer_key
        pyramid_request.params["developer_secret"] = "test_developer_secret"
        pyramid_request.feature.return_value = feature_flag

        create_application_instance(pyramid_request)

        application_instance = pyramid_request.db.query(ApplicationInstance).one()
        assert application_instance.canvas_sections_enabled == canvas_sections_enabled

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
