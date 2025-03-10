import base64

import pytest

from lms.models import ApplicationInstance, JSONSettings
from lms.models.json_settings import JSONSetting
from lms.services.aes import AESService
from tests import factories


class TestJSONSetting:
    def test_compound_key(self):
        setting = JSONSetting("group.key")

        assert setting.compound_key == "group.key"
        assert setting.group == "group"
        assert setting.key == "key"


class TestJSONSettings:
    def test_data(self, settings):
        assert settings == {"test_group": {"test_key": "test_value"}}

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
    def test_get(self, settings, group, key, default, expected_value):
        assert settings.get(group, key, default) == expected_value

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
    def test_set(self, settings, group, key, value, expected_value):
        settings.set(group, key, value)

        assert settings[group][key] == expected_value

    def test_secrets_round_trip(self, settings, aes):
        settings.set_secret(aes, "GROUP", "KEY", "VERY SECRET")

        # Value not stored as plain text
        assert settings["GROUP"]["KEY"] != "VERY_SECRET"
        # IV stored
        assert settings["GROUP"]["KEY_aes_iv"]

        assert settings.get_secret(aes, "GROUP", "KEY") == "VERY SECRET"

    def test_set_secret(self, aes_service, settings):
        settings.set_secret(aes_service, "GROUP", "KEY", "VERY SECRET")

        aes_service.build_iv.assert_called_once()
        aes_service.encrypt.assert_called_once_with(
            aes_service.build_iv.return_value, "VERY SECRET"
        )

        assert settings["GROUP"]["KEY"] == base64.b64encode(
            aes_service.encrypt.return_value
        ).decode("utf-8")
        assert settings["GROUP"]["KEY_aes_iv"] == base64.b64encode(
            aes_service.build_iv.return_value
        ).decode("utf-8")

    def test_get_secret_empty(self, settings, aes_service):
        assert not settings.get_secret(aes_service, "GROUP", "KEY")

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
            .filter(JSONSettings.matching(ApplicationInstance.settings, spec))
            .one_or_none()
        )

        assert found == ai if matches else not found

    def test__repr__(self, settings):
        assert (
            repr(settings) == "JSONSettings({'test_group': {'test_key': 'test_value'}})"
        )

    def test__str__(self, settings):
        assert (
            str(settings) == "JSONSettings({'test_group': {'test_key': 'test_value'}})"
        )

    @pytest.fixture
    def settings(self):
        return JSONSettings({"test_group": {"test_key": "test_value"}})

    @pytest.fixture
    def aes(self):
        return AESService(b"*" * 32)
