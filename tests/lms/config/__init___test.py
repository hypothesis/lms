# -*- coding: utf-8 -*-

import mock
import pytest
import pyramid.config

from lms.config import configure
from lms.config import SettingError


@pytest.mark.usefixtures(
    "env_setting",
    "groupfinder",
    "ACLAuthorizationPolicy",
    "AuthTktAuthenticationPolicy",
)
class TestConfigure:
    def test_it_returns_a_Configurator_with_the_deployment_settings_set(self, env_setting):
        configurator = configure({})

        assert isinstance(configurator, pyramid.config.Configurator)
        # Just pick some settings at random to test.
        for setting in ("jwt_secret", "google_client_id", "lms_secret"):
            assert configurator.registry.settings[setting] == env_setting.return_value

    def test_when_an_ENV_VAR_isnt_set_it_puts_None_into_the_settings(self, env_setting):
        def side_effect(envvar_name, *args, **kwargs):  # pylint: disable=unused-argument
            if envvar_name == "USERNAME":
                return None
            return mock.DEFAULT

        env_setting.side_effect = side_effect

        configurator = configure({})

        assert configurator.registry.settings["username"] is None

    def test_it_raises_if_a_required_environment_variable_is_missing(self, env_setting):
        env_setting.side_effect = SettingError("error message")

        with pytest.raises(SettingError, match="error message"):
            configure({})

    def test_the_aes_secret_setting_is_the_LMS_SECRET_env_var_as_a_byte_string(self, env_setting):
        def side_effect(envvar_name, *args, **kwargs):  # pylint: disable=unused-argument
            if envvar_name == "LMS_SECRET":
                return "test_lms_secret"
            return mock.DEFAULT

        env_setting.side_effect = side_effect

        configurator = configure({})

        assert configurator.registry.settings["aes_secret"] == b"test_lms_secret"

    def test_the_aes_secret_setting_is_truncated_to_16_chars(self, env_setting):
        env_setting.return_value = "test_lms_secret_with_more_than_16_chars"

        configurator = configure({})

        assert configurator.registry.settings["aes_secret"] == b"test_lms_secret_"

    def test_LMS_SECRET_cant_contain_non_ascii_chars(self, env_setting):
        def side_effect(envvar_name, *args, **kwargs):  # pylint: disable=unused-argument
            if envvar_name == "LMS_SECRET":
                return "test_lms_secret_\u2119"
            return mock.DEFAULT

        env_setting.side_effect = side_effect

        with pytest.raises(SettingError, match="LMS_SECRET must contain only ASCII characters"):
            configure({})

    def test_the_DATABASE_URL_envvar_becomes_the_sqlalchemy_url_setting(self, env_setting):
        def side_effect(envvar_name, *args, **kwargs):  # pylint: disable=unused-argument
            if envvar_name == "DATABASE_URL":
                return "test_database_url"
            return mock.DEFAULT

        env_setting.side_effect = side_effect

        configurator = configure({})

        assert configurator.registry.settings["sqlalchemy.url"] == "test_database_url"

    def test_the_sqlalchemy_url_setting_is_omitted_if_theres_no_DATABASE_URL(self, env_setting):
        def side_effect(envvar_name, *args, **kwargs):  # pylint: disable=unused-argument
            if envvar_name == "DATABASE_URL":
                return None
            return mock.DEFAULT

        env_setting.side_effect = side_effect

        configurator = configure({})

        # Rather than setting "sqlalchemy.url" to None as is done for any other
        # ENV_VAR, it omits it entirely.
        assert "sqlalchemy.url" not in configurator.registry.settings

    def test_trailing_slashes_are_removed_from_via_url(self, env_setting):
        def side_effect(envvar_name, *args, **kwargs):  # pylint: disable=unused-argument
            if envvar_name == "VIA_URL":
                return "https://via.hypothes.is/"
            return mock.DEFAULT

        env_setting.side_effect = side_effect

        configurator = configure({})

        assert configurator.registry.settings["via_url"] == "https://via.hypothes.is"

    def test_trailing_slashes_are_removed_from_h_api_url(self, env_setting):
        def side_effect(envvar_name, *args, **kwargs):  # pylint: disable=unused-argument
            if envvar_name == "H_API_URL":
                return "https://hypothes.is/api/"
            return mock.DEFAULT

        env_setting.side_effect = side_effect

        configurator = configure({})

        assert configurator.registry.settings["h_api_url"] == "https://hypothes.is/api"

    @pytest.mark.parametrize("envvar_value,expected_setting", [
        # Strings with spaces in them get turned into lists.
        (
            "Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef Hypothesisf6f3a575c0c73e20ab41aa6be09b9c20",
            ["Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef", "Hypothesisf6f3a575c0c73e20ab41aa6be09b9c20"],
        ),

        # A string with no spaces in it becomes a list of one.
        ("Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef", ["Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef"]),

        # Leading and trailing whitespace is ignored.
        ("Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef  ", ["Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef"]),
        ("  Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef", ["Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef"]),
        ("  Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef  ", ["Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef"]),
        (
            " Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef   Hypothesisf6f3a575c0c73e20ab41aa6be09b9c20 ",
            ["Hypothesise3f14c1f7e8c89f73cefacdd1d80d0ef", "Hypothesisf6f3a575c0c73e20ab41aa6be09b9c20"],
        ),

        # An empty string produces an empty list.
        ("", []),

        # A whitespace-only string produces an empty list.
        ("  ", []),
    ])
    def test_auto_provisioning_setting(self, env_setting, envvar_value, expected_setting):
        def side_effect(envvar_name, *args, **kwargs):  # pylint: disable=unused-argument
            if envvar_name == "AUTO_PROVISIONING":
                return envvar_value
            return mock.DEFAULT

        env_setting.side_effect = side_effect

        configurator = configure({})

        assert configurator.registry.settings["auto_provisioning"] == expected_setting

    # Pre-existing settings in the `settings` dict (which come from the *.ini
    # file) get overwritten if there's an environment variable with the same
    # setting name.
    def test_config_file_settings_are_overwritten(self, env_setting):
        configurator = configure({"jwt_secret": "original_jwt_secret"})

        assert configurator.registry.settings["jwt_secret"] != "original_jwt_secret"
        assert configurator.registry.settings["jwt_secret"] == env_setting.return_value

    # If there's an env_setting for a given setting name then, even if the
    # ENV_VAR isn't set, an ini file setting with the same name will be
    # overwritten with None.
    def test_config_file_settings_are_overwritten_with_None(self, env_setting):
        def side_effect(envvar_name, *args, **kwargs):  # pylint: disable=unused-argument
            if envvar_name == "JWT_SECRET":
                return None
            return mock.DEFAULT

        env_setting.side_effect = side_effect

        configurator = configure({"jwt_secret": "original_jwt_secret"})

        assert configurator.registry.settings["jwt_secret"] != "original_jwt_secret"
        assert configurator.registry.settings["jwt_secret"] is None

    # If there's a config file setting in the ``settings`` dict with a setting
    # name that _doesn't_ match any of the setting names used in
    # ``configure()``, then that pre-existing setting is left untouched.
    def test_config_file_settings_with_different_names_arent_removed(self):
        configurator = configure({"foo": "bar"})

        assert configurator.registry.settings["foo"] == "bar"

    def test_it_sets_the_pyramid_authentication_policy(
        self, AuthTktAuthenticationPolicy, config, env_setting, groupfinder
    ):
        def side_effect(envvar_name, *args, **kwargs):  # pylint: disable=unused-argument
            if envvar_name == "LMS_SECRET":
                return "test_lms_secret"
            return mock.DEFAULT

        env_setting.side_effect = side_effect

        configure({})

        AuthTktAuthenticationPolicy.assert_called_once_with(
            "test_lms_secret", callback=groupfinder, hashalg="sha512"
        )
        config.set_authentication_policy.assert_called_once_with(
            AuthTktAuthenticationPolicy.return_value
        )

    def test_it_sets_the_pyramid_authorization_policy(self, ACLAuthorizationPolicy, config):
        configure({})

        ACLAuthorizationPolicy.assert_called_once_with()
        config.set_authorization_policy.assert_called_once_with(
            ACLAuthorizationPolicy.return_value
        )

    @pytest.fixture
    def ACLAuthorizationPolicy(self, patch):
        return patch("lms.config.ACLAuthorizationPolicy")

    @pytest.fixture
    def AuthTktAuthenticationPolicy(self, patch):
        return patch("lms.config.AuthTktAuthenticationPolicy")

    @pytest.fixture
    def config(self, patch):
        configurator_class = patch("lms.config.Configurator")
        return configurator_class.return_value

    @pytest.fixture
    def env_setting(self, patch):
        return patch("lms.config.env_setting")

    @pytest.fixture
    def groupfinder(self, patch):
        return patch("lms.config.groupfinder")
