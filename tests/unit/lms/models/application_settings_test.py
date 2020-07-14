import pytest

from lms.models import ApplicationSettings


class TestApplicationSettings:
    def test_data(self, application_settings):
        assert application_settings == {"test_group": {"test_key": "test_value"}}

    @pytest.mark.parametrize(
        "group,key,expected_value",
        [
            # If there's a value in the data it returns it.
            ("test_group", "test_key", "test_value"),
            # If the key is missing from the data it returns None.
            ("test_group", "unknown_key", None),
            # If the entire group is missing from the data it returns None.
            ("unknown_group", "test_key", None),
        ],
    )
    def test_get(self, application_settings, group, key, expected_value):
        assert application_settings.get(group, key) == expected_value

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

    def test_clone(self, application_settings):
        cloned_settings = application_settings.clone()

        assert cloned_settings.get("test_group", "test_key") == "test_value"

        cloned_settings.set("test_group", "test_key", "new_value")
        assert application_settings.get("test_group", "test_key") == "test_value"
        assert cloned_settings.get("test_group", "test_key") == "new_value"

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
