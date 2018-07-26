# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from lms.config import settings


@pytest.mark.usefixtures('os_fixture')
class TestEnvSetting(object):

    def test_it_returns_the_value_from_the_environment_variable(self, os_fixture):
        os_fixture.environ = {'FOOBAR': 'the_value'}

        result = settings.env_setting('FOOBAR')

        assert result == 'the_value'

    def test_it_returns_none_when_environment_variable_isnt_set_and_optional(self, os_fixture):
        os_fixture.environ = {}

        result = settings.env_setting('FOOBAR')

        assert result is None

    def test_it_raises_if_the_environment_variable_isnt_set_and_required(self, os_fixture):
        os_fixture.environ = {}

        with pytest.raises(settings.SettingError) as exc_info:
            settings.env_setting('FOOBAR', required=True)
        assert str(exc_info.value) == "environment variable FOOBAR isn't set"

    def test_environment_variables_override_default_settings(self, os_fixture):
        os_fixture.environ = {'FOOBAR': 'the_value'}

        result = settings.env_setting('FOOBAR', default='DEFAULT')

        assert result == 'the_value'

    def test_if_a_default_is_given_and_theres_no_env_var_it_returns_the_default(self, os_fixture):
        os_fixture.environ = {}

        result = settings.env_setting('FOOBAR', default='DEFAULT')

        assert result == 'DEFAULT'

    def test_if_a_callback_function_is_given_it_calls_it_with_the_setting_value(self, os_fixture):
        os_fixture.environ = {'FOOBAR': 'the_value'}
        callback = mock.MagicMock()

        settings.env_setting('FOOBAR', callback=callback)

        callback.assert_called_once_with('the_value')

    def test_if_a_callback_function_is_given_it_returns_what_the_callback_returns(self, os_fixture):
        os_fixture.environ = {'FOOBAR': 'the_value'}
        callback = mock.MagicMock()

        result = settings.env_setting('FOOBAR', callback=callback)

        assert result == callback.return_value

    def test_default_values_are_passed_to_callback_functions(self, os_fixture):
        os_fixture.environ = {}
        callback = mock.MagicMock()

        settings.env_setting('FOOBAR', callback=callback, default='default_value')

        callback.assert_called_once_with('default_value')

    def test_None_is_passed_to_callback_if_setting_is_missing_and_theres_no_default(self, os_fixture):
        os_fixture.environ = {}
        callback = mock.MagicMock()

        settings.env_setting('FOOBAR', callback=callback)

        callback.assert_called_once_with(None)

    def test_callback_isnt_called_if_required_setting_is_missing(self, os_fixture):
        os_fixture.environ = {}
        callback = mock.MagicMock()

        try:
            settings.env_setting('FOOBAR', required=True, callback=callback)
        except Exception:  # pylint: disable=broad-except
            pass

        callback.assert_not_called()


@pytest.fixture
def os_fixture(patch):
    return patch('lms.config.settings.os')
