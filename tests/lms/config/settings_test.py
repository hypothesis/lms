import pytest

from lms.config.settings import SettingError, SettingGetter


@pytest.mark.usefixtures("os_fixture")
class TestSettingGetter:
    @pytest.mark.parametrize(
        "environ,settings,envvar_name,required,default,expected",
        [
            ({"FOO_BAR": "from_environ"}, {}, "FOO_BAR", False, None, "from_environ"),
            ({"FOO_BAR": "from_environ"}, {}, "FOO_BAR", True, None, "from_environ"),
            (
                {"FOO_BAR": "from_environ"},
                {"foo_bar": "from_config_file"},
                "FOO_BAR",
                False,
                None,
                "from_environ",
            ),
            (
                {"FOO_BAR": "from_environ"},
                {"foo_bar": "from_config_file"},
                "FOO_BAR",
                True,
                None,
                "from_environ",
            ),
            (
                {"FOO_BAR": "from_environ"},
                {"foo_bar": "from_config_file"},
                "FOO_BAR",
                False,
                "default",
                "from_environ",
            ),
            (
                {"FOO_BAR": "from_environ"},
                {"foo_bar": "from_config_file"},
                "FOO_BAR",
                True,
                "default",
                "from_environ",
            ),
            (
                {"FOO_BAR": "from_environ"},
                {},
                "FOO_BAR",
                False,
                "default",
                "from_environ",
            ),
            (
                {"FOO_BAR": "from_environ"},
                {},
                "FOO_BAR",
                True,
                "default",
                "from_environ",
            ),
            (
                {},
                {"foo_bar": "from_config_file"},
                "FOO_BAR",
                False,
                None,
                "from_config_file",
            ),
            (
                {},
                {"foo_bar": "from_config_file"},
                "FOO_BAR",
                True,
                None,
                "from_config_file",
            ),
            (
                {},
                {"foo_bar": "from_config_file"},
                "FOO_BAR",
                False,
                "default",
                "from_config_file",
            ),
            (
                {},
                {"foo_bar": "from_config_file"},
                "FOO_BAR",
                True,
                "default",
                "from_config_file",
            ),
            ({}, {}, "FOO_BAR", False, "default", "default"),
            ({}, {}, "FOO_BAR", True, "default", "default"),
            ({}, {}, "FOO_BAR", False, None, None),
        ],
    )
    def test_it(
        self, os_fixture, environ, settings, envvar_name, required, default, expected
    ):
        os_fixture.environ = environ
        sg = SettingGetter(settings)

        assert sg.get(envvar_name, required=required, default=default) == expected

    def test_it_raises_if_a_required_setting_with_no_default_is_missing(
        self, os_fixture
    ):
        os_fixture.environ = {}
        sg = SettingGetter({})

        with pytest.raises(
            SettingError, match="Required setting FOO_BAR / foo_bar isn't set"
        ):
            sg.get("FOO_BAR", required=True)

    @pytest.fixture
    def os_fixture(self, patch):
        return patch("lms.config.settings.os")
