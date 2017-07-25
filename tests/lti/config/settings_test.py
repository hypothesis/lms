# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from lti.config.settings import (
    SettingError,
    env_setting,
)


@pytest.mark.usefixtures('os_fixture')
class TestEnvSetting(object):

    def test_it_returns_the_value_from_the_environment_variable(self, os_fixture):
        os_fixture.environ = {'FOOBAR': 'the_value'}

        result = env_setting('FOOBAR')

        assert result == 'the_value'

    def test_it_raises_if_the_environment_variable_isnt_set(self, os_fixture):
        os_fixture.environ = {}

        with pytest.raises(SettingError) as exc_info:
            env_setting('FOOBAR')

        assert exc_info.value.message == "environment variable FOOBAR isn't set"


@pytest.fixture
def os_fixture(patch):
    return patch('lti.config.settings.os')
