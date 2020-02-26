import pytest

from lms.models import ApplicationInstance
from lms.views.application_instances import create_application_instance, new_application_instance


class TestCreateApplicationInstance:
    def test_it_creates_an_application_instance(self, pyramid_request):
        create_application_instance(pyramid_request)

        ai = pyramid_request.db.query(ApplicationInstance).one()
        assert ai.lms_url == "canvas.example.com"
        assert ai.requesters_email == "email@example.com"
        assert ai.developer_key is None
        assert ai.developer_secret is None

    def test_it_saves_the_Canvas_developer_key_and_secret_if_given(
        self, pyramid_request
    ):
        pyramid_request.params["developer_key"] = "example_key"
        pyramid_request.params["developer_secret"] = "example_secret"

        create_application_instance(pyramid_request)

        ai = pyramid_request.db.query(ApplicationInstance).one()
        assert ai.developer_key == "example_key"
        assert ai.developer_secret

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

        ai = pyramid_request.db.query(ApplicationInstance).one()
        assert ai.developer_key is None
        assert ai.developer_secret is None

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
