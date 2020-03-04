import pytest

from lms.config.settings import SettingGetter


@pytest.mark.usefixtures("os_fixture")
class TestSettingGetter:
    @pytest.mark.parametrize(
        "environ,settings,envvar_name,default,expected",
        [
            ({"FOO_BAR": "from_environ"}, {}, "FOO_BAR", None, "from_environ"),
            ({"FOO_BAR": "from_environ"}, {}, "FOO_BAR", None, "from_environ"),
            (
                {"FOO_BAR": "from_environ"},
                {"foo_bar": "from_config_file"},
                "FOO_BAR",
                None,
                "from_environ",
            ),
            (
                {"FOO_BAR": "from_environ"},
                {"foo_bar": "from_config_file"},
                "FOO_BAR",
                None,
                "from_environ",
            ),
            (
                {"FOO_BAR": "from_environ"},
                {"foo_bar": "from_config_file"},
                "FOO_BAR",
                "default",
                "from_environ",
            ),
            (
                {"FOO_BAR": "from_environ"},
                {"foo_bar": "from_config_file"},
                "FOO_BAR",
                "default",
                "from_environ",
            ),
            ({"FOO_BAR": "from_environ"}, {}, "FOO_BAR", "default", "from_environ"),
            ({"FOO_BAR": "from_environ"}, {}, "FOO_BAR", "default", "from_environ"),
            ({}, {"foo_bar": "from_config_file"}, "FOO_BAR", None, "from_config_file"),
            ({}, {"foo_bar": "from_config_file"}, "FOO_BAR", None, "from_config_file"),
            (
                {},
                {"foo_bar": "from_config_file"},
                "FOO_BAR",
                "default",
                "from_config_file",
            ),
            (
                {},
                {"foo_bar": "from_config_file"},
                "FOO_BAR",
                "default",
                "from_config_file",
            ),
            ({}, {}, "FOO_BAR", "default", "default"),
            ({}, {}, "FOO_BAR", "default", "default"),
            ({}, {}, "FOO_BAR", None, None),
        ],
    )
    def test_it(self, os_fixture, environ, settings, envvar_name, default, expected):
        os_fixture.environ = environ
        settings_getter = SettingGetter(settings)

        assert settings_getter.get(envvar_name, default=default) == expected

    @pytest.fixture
    def os_fixture(self, patch):
        return patch("lms.config.settings.os")
