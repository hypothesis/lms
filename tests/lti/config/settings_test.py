# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from lti.config import settings


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


@pytest.fixture
def os_fixture(patch):
    return patch('lti.config.settings.os')
