import base64

import pytest

from lms.models import ApplicationInstance, ApplicationSettings
from lms.services.aes import AESService
from tests import factories


class TestApplicationSettings:
    def test_data(self, application_settings):
        assert application_settings == {"test_group": {"test_key": "test_value"}}

    @pytest.mark.parametrize(
        "group,key,default,expected_value",
        [
            # If there's a value in the data it returns it.
            ("test_group", "test_key", None, "test_value"),
            # If the key is missing from the data it returns None.
            ("test_group", "unknown_key", None, None),
            # If the entire group is missing from the data it returns None.
            ("unknown_group", "test_key", None, None),
            # Ignores default if key is present
            ("test_group", "test_key", "DEFAULT", "test_value"),
            # If the key is missing from the data it returns the default
            ("test_group", "unknown_key", "DEFAULT", "DEFAULT"),
            # If the entire group is missing from the data it also returns the default
            ("unknown_group", "test_key", "DEFAULT", "DEFAULT"),
        ],
    )
    def test_get(self, application_settings, group, key, default, expected_value):
        assert application_settings.get(group, key, default) == expected_value

    @pytest.mark.parametrize(
        "group,key,value,expected_value",
        [
            # Inserting a new key into an existing group.
            ("test_group", "new_key", "new_value", "new_value"),
            # Overwriting an existing key.
            ("test_group", "test_key", "new_value", "new_value"),
            # It creates the group if it's missing.
            ("missing_group", "new_key", "new_value", "new_value"),
        ],
    )
    def test_set(self, application_settings, group, key, value, expected_value):
        application_settings.set(group, key, value)

        assert application_settings[group][key] == expected_value

    def test_secrets_round_trip(self, application_settings, aes):
        application_settings.set_secret(aes, "GROUP", "KEY", "VERY SECRET")

        # Value not stored as plain text
        assert application_settings["GROUP"]["KEY"] != "VERY_SECRET"
        # IV stored
        assert application_settings["GROUP"]["KEY_aes_iv"]

        assert application_settings.get_secret(aes, "GROUP", "KEY") == "VERY SECRET"

    def test_set_secret(self, aes_service, application_settings):
        application_settings.set_secret(aes_service, "GROUP", "KEY", "VERY SECRET")

        aes_service.build_iv.assert_called_once()
        aes_service.encrypt.assert_called_once_with(
            aes_service.build_iv.return_value, "VERY SECRET"
        )

        assert application_settings["GROUP"]["KEY"] == base64.b64encode(
            aes_service.encrypt.return_value
        ).decode("utf-8")
        assert application_settings["GROUP"]["KEY_aes_iv"] == base64.b64encode(
            aes_service.build_iv.return_value
        ).decode("utf-8")

    def test_get_secret_empty(self, application_settings, aes_service):
        assert not application_settings.get_secret(aes_service, "GROUP", "KEY")

    @pytest.mark.parametrize(
        "spec,matches",
        (
            ({"group.key": "value"}, True),
            ({"group.key": ...}, True),
            ({"group": ...}, True),
            ({"group.key": "WRONG_VALUE"}, False),
            ({"group.WRONG_KEY": ...}, False),
            ({"WRONG_GROUP": ...}, False),
        ),
    )
    def test_matching(self, db_session, spec, matches):
        # We'll use an application instance as a host
        ai = factories.ApplicationInstance(settings={"group": {"key": "value"}})

        found = (
            db_session.query(ApplicationInstance)
            .filter(ApplicationSettings.matching(ApplicationInstance.settings, spec))
            .one_or_none()
        )

        assert found == ai if matches else not found

    def test__repr__(self, application_settings):
        assert (
            repr(application_settings)
            == "ApplicationSettings({'test_group': {'test_key': 'test_value'}})"
        )

    def test__str__(self, application_settings):
        assert (
            str(application_settings)
            == "ApplicationSettings({'test_group': {'test_key': 'test_value'}})"
        )

    @pytest.fixture
    def application_settings(self):
        return ApplicationSettings({"test_group": {"test_key": "test_value"}})

    @pytest.fixture
    def aes(self):
        return AESService(b"*" * 32)
