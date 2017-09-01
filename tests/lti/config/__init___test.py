# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from lti.config import (
    SettingError,
    configure,
)


@pytest.mark.usefixtures('env_setting')
class TestConfigure(object):

    def test_it_raises_if_env_setting_raises(self, env_setting):
        env_setting.side_effect = SettingError()

        with pytest.raises(SettingError):
            configure()

    def test_it_returns_a_Configurator_with_all_the_settings(self,
                                                             env_setting):
        def env_setting_side_effect(envvar_name, required=False, default=None):  # pylint:disable=unused-argument
            return {
                'LTI_FILES_PATH': 'the_lti_files_path_setting',
                'LTI_SERVER': 'the_lti_server_setting',
                'LTI_CREDENTIALS_URL':  'the_lti_credentials_url_setting',
                'DATABASE_URL': 'the_database_url',
                'VIA_URL': 'the_via_url',
            }[envvar_name]

        env_setting.side_effect = env_setting_side_effect

        config = configure()

        assert config.registry.settings['lti_server'] == 'the_lti_server_setting'
        assert config.registry.settings['lti_credentials_url'] == 'the_lti_credentials_url_setting'
        assert config.registry.settings['sqlalchemy.url'] == 'the_database_url'
        assert config.registry.settings['via_url'] == 'the_via_url'

    @pytest.fixture
    def env_setting(self, patch):
        return patch('lti.config.env_setting')
