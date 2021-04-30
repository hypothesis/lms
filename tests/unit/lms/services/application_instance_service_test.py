from unittest import mock

import pytest

from lms.models import ApplicationInstance
from lms.services.application_instance import factory
from tests import factories


class TestApplicationInstanceGetter:
    def test_get_one(self, ai_service, test_application_instance):
        assert ai_service.get(test_application_instance.id) == test_application_instance

    def test_get_none(self, ai_service):
        assert ai_service.get(1000000) is None

    def test_get_find_by_id_one(self, ai_service, test_application_instance):
        assert (
            ai_service.find(str(test_application_instance.id))
            == test_application_instance
        )

    def test_get_find_by_consumer_key_one(self, ai_service, test_application_instance):
        assert (
            ai_service.find(test_application_instance.consumer_key)
            == test_application_instance
        )

    def test_update_settings_no_update(
        self, ai_service, test_application_instance, db_session
    ):
        ai_service.update_settings(test_application_instance)

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
        ai_service,
        test_application_instance,
        db_session,
    ):
        ai_service.update_settings(test_application_instance, **{setting_name: True})

        # Let's re-query to get the state form the DB
        ai = db_session.query(ApplicationInstance).get(test_application_instance.id)
        assert ai.settings.get(*setting_location.split(".")) is True

        ai_service.update_settings(test_application_instance, **{setting_name: False})

        # Re-query again
        ai = db_session.query(ApplicationInstance).get(test_application_instance.id)
        assert (
            # pylint: disable=compare-to-zero
            ai.settings.get(*setting_location.split("."))
            is False
        )

    @pytest.fixture
    def ai_service(self, pyramid_request):
        return factory(mock.sentinel.context, pyramid_request)

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
