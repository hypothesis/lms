from unittest import mock

import pytest

from lms.models import ApplicationInstance
from lms.services import ConsumerKeyError
from lms.services.application_instance import factory
from tests import factories


class TestApplicationInstanceService:
    def test_get_one(self, svc, test_application_instance):
        assert (
            svc.get(test_application_instance.consumer_key) == test_application_instance
        )

    def test_get_with_default_consumer_key(self, svc, default_application_instance):
        assert svc.get() == default_application_instance

    def test_get_raises_ConsumerKeyError_if_consumer_key_doesnt_exist(self, svc):
        with pytest.raises(ConsumerKeyError):
            assert svc.get("NOPE") is None

    def test_get_raises_ConsumerKeyError_if_consumer_key_is_None(self, pyramid_request):
        pyramid_request.lti_user = None
        svc = factory(mock.sentinel.context, pyramid_request)

        with pytest.raises(ConsumerKeyError):
            svc.get(None)

    def test_update_settings_no_update(
        self, svc, test_application_instance, db_session
    ):
        svc.update_settings(test_application_instance)

        # Let's re-query to get the state form the DB
        ai = db_session.query(ApplicationInstance).get(test_application_instance.id)

        assert ai.settings == test_application_instance.settings

    @pytest.mark.parametrize(
        "setting_name,setting_location",
        [
            ("canvas_sections_enabled", "canvas.sections_enabled"),
            ("canvas_groups_enabled", "canvas.groups_enabled"),
        ],
    )
    def test_update_settings_boolean_toggle(
        self,
        setting_name,
        setting_location,
        svc,
        test_application_instance,
        db_session,
    ):
        svc.update_settings(test_application_instance, **{setting_name: True})

        # Let's re-query to get the state form the DB
        ai = db_session.query(ApplicationInstance).get(test_application_instance.id)
        assert ai.settings.get(*setting_location.split(".")) is True

        svc.update_settings(test_application_instance, **{setting_name: False})

        # Re-query again
        ai = db_session.query(ApplicationInstance).get(test_application_instance.id)
        assert (
            # pylint: disable=compare-to-zero
            ai.settings.get(*setting_location.split("."))
            is False
        )

    @pytest.fixture
    def svc(self, pyramid_request):
        return factory(mock.sentinel.context, pyramid_request)

    @pytest.fixture(autouse=True)
    def default_application_instance(self, db_session, pyramid_request):
        ai = factories.ApplicationInstance(
            consumer_key=pyramid_request.lti_user.oauth_consumer_key
        )
        db_session.flush()
        return ai

    @pytest.fixture(autouse=True)
    def test_application_instance(self, db_session):
        ai = factories.ApplicationInstance()
        db_session.flush()
        return ai

    @pytest.fixture(autouse=True)
    def application_instances(self):
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
