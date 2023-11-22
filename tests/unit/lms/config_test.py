import pyramid.config
import pytest

from lms.config import SETTINGS, SettingError, configure


class TestConfigure:
    # These are settings with no special tricks
    NORMAL_SETTINGS = {
        setting
        for setting in SETTINGS
        if not setting.value_mapper and setting.read_from == setting.name
    }

    def test_it(self):
        configurator = configure({})

        assert isinstance(configurator, pyramid.config.Configurator)

    def test_it_reads_from_environment_in_preference(self, config_file):
        configurator = configure(config_file)

        expected = {setting.name: "env" for setting in self.NORMAL_SETTINGS}
        for param, value in expected.items():
            assert configurator.registry.settings[param] == value

    def test_it_will_read_from_the_config_file(self, environ, config_file):
        environ.clear()

        configurator = configure(config_file)

        expected = {setting.name: "config_file" for setting in self.NORMAL_SETTINGS}
        for param, value in expected.items():
            assert configurator.registry.settings[param] == value

    def test_it_keeps_settings_we_dont_know_about(self):
        configurator = configure({"new": "value"})

        assert configurator.registry.settings["new"] == "value"

    @pytest.mark.parametrize(
        "setting,value,expected",
        (
            ("via_url", "url", "url/"),
            ("via_url", "url/", "url/"),
            ("h_api_url_private", "url", "url/"),
            ("h_api_url_private", "url/", "url/"),
            ("h_api_url_public", "url", "url/"),
            ("h_api_url_public", "url/", "url/"),
            ("dev", "", False),
            ("dev", "false", False),
            ("dev", "1", True),
            ("rpc_allowed_origins", None, []),
            ("rpc_allowed_origins", "", []),
            ("rpc_allowed_origins", "a", ["a"]),
            ("rpc_allowed_origins", "a\nb\nc", ["a", "b", "c"]),
        ),
    )
    def test_it_with_mapped_values(self, environ, setting, value, expected):
        environ[setting.upper()] = value

        assert configure({}).registry.settings[setting] == expected

    @pytest.mark.parametrize(
        "lms_secret,aes_secret",
        (
            ("short", b"short"),
            ("---4---8--12--16--20--24", b"---4---8--12--16"),
            (None, None),
        ),
    )
    def test_it_gets_aes_secret(self, environ, lms_secret, aes_secret):
        environ["LMS_SECRET"] = lms_secret

        assert configure({}).registry.settings["aes_secret"] == aes_secret

    def test_it_aes_secret_raises_for_non_ascii(self, environ):
        environ["LMS_SECRET"] = "\u2119"

        with pytest.raises(SettingError):
            configure({})

    @pytest.fixture
    def config_file(self):
        return {setting.read_from: "config_file" for setting in SETTINGS}

    @pytest.fixture(autouse=True)
    def environ(self, patch):
        os = patch("lms.config.os")
        os.environ = {setting.read_from.upper(): "env" for setting in SETTINGS}
        return os.environ
