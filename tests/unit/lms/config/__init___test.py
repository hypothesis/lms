from __future__ import unicode_literals

from unittest import mock

import pyramid.config
import pytest

from lms.config import SettingError, configure


@pytest.mark.usefixtures("SettingGetter", "ACLAuthorizationPolicy")
class TestConfigure:
    def test_it_returns_a_Configurator_with_the_deployment_settings_set(
        self, setting_getter
    ):
        configurator = configure({})

        assert isinstance(configurator, pyramid.config.Configurator)
        # Just pick some settings at random to test.
        for setting in ("jwt_secret", "google_client_id", "lms_secret"):
            assert (
                configurator.registry.settings[setting]
                == setting_getter.get.return_value
            )

    def test_when_an_ENV_VAR_isnt_set_it_puts_None_into_the_settings(
        self, setting_getter
    ):
        def side_effect(
            envvar_name, *args, **kwargs
        ):  # pylint: disable=unused-argument
            if envvar_name == "USERNAME":
                return None
            return mock.DEFAULT

        setting_getter.get.side_effect = side_effect

        configurator = configure({})

        assert configurator.registry.settings["username"] is None

    def test_it_raises_if_a_required_environment_variable_is_missing(
        self, setting_getter
    ):
        setting_getter.get.side_effect = SettingError("error message")

        with pytest.raises(SettingError, match="error message"):
            configure({})

    def test_dev_defaults_to_False(self, setting_getter):
        def get(envvar_name, *_args, **_kwargs):
            if envvar_name == "DEV":
                return None
            return mock.DEFAULT

        setting_getter.get.side_effect = get

        configurator = configure({})

        assert not configurator.registry.settings["dev"]

    def test_dev_can_be_set_to_True(self, setting_getter):
        def get(envvar_name, *_args, **_kwargs):
            if envvar_name == "DEV":
                return "true"
            return mock.DEFAULT

        setting_getter.get.side_effect = get

        configurator = configure({})

        assert configurator.registry.settings["dev"] is True

    def test_the_aes_secret_setting_is_the_LMS_SECRET_env_var_as_a_byte_string(
        self, setting_getter
    ):
        def side_effect(
            envvar_name, *args, **kwargs
        ):  # pylint: disable=unused-argument
            if envvar_name == "LMS_SECRET":
                return "test_lms_secret"
            return mock.DEFAULT

        setting_getter.get.side_effect = side_effect

        configurator = configure({})

        assert configurator.registry.settings["aes_secret"] == b"test_lms_secret"

    def test_the_aes_secret_setting_is_truncated_to_16_chars(self, setting_getter):
        setting_getter.get.return_value = "test_lms_secret_with_more_than_16_chars"

        configurator = configure({})

        assert configurator.registry.settings["aes_secret"] == b"test_lms_secret_"

    def test_aes_secret_is_None_when_theres_no_LMS_SECRET(self, setting_getter):
        def side_effect(envvar_name, *_args, **_kwargs):
            if envvar_name == "LMS_SECRET":
                return None
            return mock.DEFAULT

        setting_getter.get.side_effect = side_effect

        configurator = configure({})

        assert configurator.registry.settings["aes_secret"] is None

    def test_LMS_SECRET_cant_contain_non_ascii_chars(self, setting_getter):
        def side_effect(
            envvar_name, *args, **kwargs
        ):  # pylint: disable=unused-argument
            if envvar_name == "LMS_SECRET":
                return "test_lms_secret_\u2119"
            return mock.DEFAULT

        setting_getter.get.side_effect = side_effect

        with pytest.raises(
            SettingError, match="LMS_SECRET must contain only ASCII characters"
        ):
            configure({})

    def test_the_DATABASE_URL_envvar_becomes_the_sqlalchemy_url_setting(
        self, setting_getter
    ):
        def side_effect(
            envvar_name, *args, **kwargs
        ):  # pylint: disable=unused-argument
            if envvar_name == "DATABASE_URL":
                return "test_database_url"
            return mock.DEFAULT

        setting_getter.get.side_effect = side_effect

        configurator = configure({})

        assert configurator.registry.settings["sqlalchemy.url"] == "test_database_url"

    def test_the_sqlalchemy_url_setting_is_omitted_if_theres_no_DATABASE_URL(
        self, setting_getter
    ):
        def side_effect(
            envvar_name, *args, **kwargs
        ):  # pylint: disable=unused-argument
            if envvar_name == "DATABASE_URL":
                return None
            return mock.DEFAULT

        setting_getter.get.side_effect = side_effect

        configurator = configure({})

        # Rather than setting "sqlalchemy.url" to None as is done for any other
        # ENV_VAR, it omits it entirely.
        assert "sqlalchemy.url" not in configurator.registry.settings

    def test_trailing_slashes_are_appended_to_via_url(self, setting_getter):
        def side_effect(
            envvar_name, *args, **kwargs
        ):  # pylint: disable=unused-argument
            if envvar_name == "VIA_URL":
                return "https://via3.hypothes.is"
            return mock.DEFAULT

        setting_getter.get.side_effect = side_effect

        configurator = configure({})

        assert configurator.registry.settings["via_url"] == "https://via3.hypothes.is/"

    def test_trailing_slashes_are_appended_to_legacy_via_url(self, setting_getter):
        def side_effect(
            envvar_name, *args, **kwargs
        ):  # pylint: disable=unused-argument
            if envvar_name == "LEGACY_VIA_URL":
                return "https://via.hypothes.is"
            return mock.DEFAULT

        setting_getter.get.side_effect = side_effect

        configurator = configure({})

        assert (
            configurator.registry.settings["legacy_via_url"]
            == "https://via.hypothes.is/"
        )

    def test_trailing_slashes_are_appended_to_h_api_url_public(self, setting_getter):
        def side_effect(
            envvar_name, *args, **kwargs
        ):  # pylint: disable=unused-argument
            if envvar_name == "H_API_URL_PUBLIC":
                return "https://hypothes.is/api"
            return mock.DEFAULT

        setting_getter.get.side_effect = side_effect

        configurator = configure({})

        assert (
            configurator.registry.settings["h_api_url_public"]
            == "https://hypothes.is/api/"
        )

    def test_trailing_slashes_are_appended_to_h_api_url_private(self, setting_getter):
        def side_effect(
            envvar_name, *args, **kwargs
        ):  # pylint: disable=unused-argument
            if envvar_name == "H_API_URL_PRIVATE":
                return "https://hypothes.is/api"
            return mock.DEFAULT

        setting_getter.get.side_effect = side_effect

        configurator = configure({})

        assert (
            configurator.registry.settings["h_api_url_private"]
            == "https://hypothes.is/api/"
        )

    @pytest.mark.parametrize(
        "envvar_value,expected_setting",
        [
            # Strings with spaces in them get turned into lists.
            (
                "https://example.com https://hypothes.is",
                ["https://example.com", "https://hypothes.is"],
            ),
            # A string with no spaces in it becomes a list of one.
            ("https://example.com", ["https://example.com"]),
            # Leading and trailing whitespace is ignored.
            ("https://example.com  ", ["https://example.com"]),
            ("  https://example.com", ["https://example.com"]),
            ("  https://example.com  ", ["https://example.com"]),
            (
                " https://example.com   https://hypothes.is ",
                ["https://example.com", "https://hypothes.is"],
            ),
            # An empty string produces an empty list.
            ("", []),
            # A whitespace-only string produces an empty list.
            ("  ", []),
        ],
    )
    def test_rpc_allowed_origins_setting(
        self, setting_getter, envvar_value, expected_setting
    ):
        def side_effect(
            envvar_name, *args, **kwargs
        ):  # pylint: disable=unused-argument
            if envvar_name == "RPC_ALLOWED_ORIGINS":
                return envvar_value
            return mock.DEFAULT

        setting_getter.get.side_effect = side_effect

        configurator = configure({})

        assert configurator.registry.settings["rpc_allowed_origins"] == expected_setting

    # Pre-existing settings in the `settings` dict (which come from the *.ini
    # file) get overwritten if there's an environment variable with the same
    # setting name.
    def test_config_file_settings_are_overwritten(self, setting_getter):
        configurator = configure({"jwt_secret": "original_jwt_secret"})

        assert configurator.registry.settings["jwt_secret"] != "original_jwt_secret"
        assert (
            configurator.registry.settings["jwt_secret"]
            == setting_getter.get.return_value
        )

    # If there's a config file setting in the ``settings`` dict with a setting
    # name that _doesn't_ match any of the setting names used in
    # ``configure()``, then that pre-existing setting is left untouched.
    def test_config_file_settings_with_different_names_arent_removed(self):
        configurator = configure({"foo": "bar"})

        assert configurator.registry.settings["foo"] == "bar"

    def test_it_sets_the_pyramid_authorization_policy(
        self, ACLAuthorizationPolicy, config
    ):
        configure({})

        ACLAuthorizationPolicy.assert_called_once_with()
        config.set_authorization_policy.assert_called_once_with(
            ACLAuthorizationPolicy.return_value
        )

    @pytest.fixture
    def ACLAuthorizationPolicy(self, patch):
        return patch("lms.config.ACLAuthorizationPolicy")

    @pytest.fixture
    def config(self, patch):
        configurator_class = patch("lms.config.Configurator")
        return configurator_class.return_value

    @pytest.fixture
    def SettingGetter(self, patch):
        return patch("lms.config.SettingGetter")

    @pytest.fixture
    def setting_getter(self, SettingGetter):
        return SettingGetter.return_value
