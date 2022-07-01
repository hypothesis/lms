from dataclasses import asdict

from h_matchers import Any

from lms.product.plugin import PluginConfig, Plugins


class TestPlugins:
    def test_instantiation(self, pyramid_request, mock_service):
        plugin_config = PluginConfig()
        # We re-use pyramid services, so we can make use of our mock service
        # fixture to register the services mentioned in the default
        # `PluginConfig` object.
        expected_attrs = {
            plugin_name: mock_service(plugin_class)
            for plugin_name, plugin_class in asdict(plugin_config).items()
        }

        plugins = Plugins(pyramid_request, plugin_config)

        assert plugins == Any.instance_of(Plugins).with_attrs(expected_attrs)
