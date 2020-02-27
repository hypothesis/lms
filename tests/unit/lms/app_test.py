from unittest import mock

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
    def test_it_doesnt_crash(self, pyramid_config):
        create_app(pyramid_config)


@pytest.fixture(autouse=True)
def configure(patch):
    return patch("lms.app.configure")
