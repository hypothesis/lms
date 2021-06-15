from unittest import mock

import pytest

from lms.models import ApplicationInstance
from lms.services import ConsumerKeyError
from lms.services.application_instance import factory
from tests import factories
from tests.conftest import TEST_SETTINGS


class TestApplicationInstanceService:
    def test_get_one(self, svc, application_instance):
        assert svc.get(application_instance.consumer_key) == application_instance

    def test_get_with_default_consumer_key(
        self, svc, application_instance, pyramid_request
    ):
        # Make sure the DB *does* contain an ApplicationInstance matching the
        # request's consumer key.
        application_instance.consumer_key = pyramid_request.lti_user.oauth_consumer_key

        assert svc.get() == application_instance

    def test_get_raises_ConsumerKeyError_if_consumer_key_doesnt_exist(self, svc):
        with pytest.raises(ConsumerKeyError):
            assert svc.get("NOPE") is None

    def test_get_raises_ConsumerKeyError_if_consumer_key_is_None(self, pyramid_request):
        pyramid_request.lti_user = None
        svc = factory(mock.sentinel.context, pyramid_request)

        with pytest.raises(ConsumerKeyError):
            svc.get(None)

    def test_create(self, svc, new_application_instance_params, db_session):
        ai = svc.create(**new_application_instance_params)
        db_session.flush()

        ai = db_session.query(ApplicationInstance).get(ai.id)
        assert ai.lms_url == "canvas.example.com"
        assert ai.requesters_email == "email@example.com"
        assert ai.developer_key is None
        assert ai.developer_secret is None

    def test_create_saves_the_Canvas_developer_key_and_secret_if_given(
        self, svc, new_application_instance_params, db_session
    ):
        new_application_instance_params["developer_key"] = "example_key"
        new_application_instance_params["developer_secret"] = "example_secret"

        ai = svc.create(**new_application_instance_params)
        db_session.flush()

        ai = db_session.query(ApplicationInstance).get(ai.id)
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
    def test_create_if_developer_key_or_secret_is_missing_it_doesnt_save_either(
        self,
        developer_key,
        developer_secret,
        svc,
        new_application_instance_params,
        db_session,
    ):
        new_application_instance_params["developer_key"] = developer_key
        new_application_instance_params["developer_secret"] = developer_secret

        ai = svc.create(**new_application_instance_params)
        db_session.flush()

        ai = db_session.query(ApplicationInstance).get(ai.id)
        assert ai.developer_key is None
        assert ai.developer_secret is None

    @pytest.mark.parametrize(
        "developer_key,canvas_sections_enabled",
        [("test_developer_key", True), ("", False)],
    )
    def test_create_sets_canvas_sections_enabled(
        self,
        developer_key,
        canvas_sections_enabled,
        svc,
        new_application_instance_params,
        db_session,
    ):
        new_application_instance_params["developer_secret"] = "example_secret"
        new_application_instance_params["developer_key"] = developer_key

        ai = svc.create(**new_application_instance_params)
        db_session.flush()

        ai = db_session.query(ApplicationInstance).get(ai.id)
        assert (
            bool(ai.settings.get("canvas", "sections_enabled"))
            == canvas_sections_enabled
        )

    @pytest.fixture
    def svc(self, pyramid_request):
        return factory(mock.sentinel.context, pyramid_request)

    @pytest.fixture(autouse=True)
    def application_instance(self, db_session):
        ai = factories.ApplicationInstance()
        db_session.flush()
        return ai

    @pytest.fixture
    def new_application_instance_params(self):
        return {
            "lms_url": "canvas.example.com",
            "email": "email@example.com",
            "developer_key": "",
            "developer_secret": "",
            "aes_secret": TEST_SETTINGS["aes_secret"],
        }

    @pytest.fixture(autouse=True)
    def noise_application_instances(self):
        """Add some "noise" application instances."""
        # Add some "noise" application instances to the DB for every test, to
        # make the tests more realistic.
        factories.ApplicationInstance.create_batch(size=3)


class TestFactory:
    def test_it(self, ApplicationInstanceService, pyramid_request):
        application_instance_service = factory(mock.sentinel.context, pyramid_request)

        ApplicationInstanceService.assert_called_once_with(
            pyramid_request.db, pyramid_request.lti_user.oauth_consumer_key
        )
        assert application_instance_service == ApplicationInstanceService.return_value

    def test_it_with_no_lti_user(self, ApplicationInstanceService, pyramid_request):
        pyramid_request.lti_user = None

        application_instance_service = factory(mock.sentinel.context, pyramid_request)

        ApplicationInstanceService.assert_called_once_with(pyramid_request.db, None)
        assert application_instance_service == ApplicationInstanceService.return_value

    @pytest.fixture(autouse=True)
    def ApplicationInstanceService(self, patch):
        return patch("lms.services.application_instance.ApplicationInstanceService")
