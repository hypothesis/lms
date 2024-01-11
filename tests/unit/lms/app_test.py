from unittest import mock
from unittest.mock import sentinel

import pytest

from lms.app import configure_jinja2_assets, create_app


class TestConfigureJinja2Assets:
    def test_it_adds_the_static_asset_url_generator_functions_to_the_template_env(
        self, pyramid_config
    ):
        assets_env = pyramid_config.registry["assets_env"] = mock.Mock(
            spec_set=["url", "urls"]
        )

        configure_jinja2_assets(pyramid_config)

        assert (
            pyramid_config.get_jinja2_environment().globals["asset_url"]
            == assets_env.url
        )
        assert (
            pyramid_config.get_jinja2_environment().globals["asset_urls"]
            == assets_env.urls
        )


class TestCreateApp:
    def test_it(self, configure, Regions):
        settings = {"key": "value"}

        create_app(sentinel.pyramid_config, **settings)

        configure.assert_called_once_with(settings=settings)
        Regions.set_region.assert_called_once_with(
            sentinel.h_authority, sentinel.region_code
        )

    @pytest.fixture(autouse=True)
    def registry(self, configure):
        registry = configure.return_value.registry
        registry.settings = {
            "h_authority": sentinel.h_authority,
            "region_code": sentinel.region_code,
            "lms_secret": sentinel.lms_secret,
            "admin_auth_google_client_id": sentinel.admin_auth_google_client_id,
            "admin_auth_google_client_secret": sentinel.admin_auth_google_client_secret,
        }
        return registry

    @pytest.fixture(autouse=True)
    def Regions(self, patch):
        return patch("lms.app.Regions")

    @pytest.fixture(autouse=True)
    def configure(self, patch):
        return patch("lms.app.configure")
