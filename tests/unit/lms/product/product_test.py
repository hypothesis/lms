from dataclasses import dataclass, fields
from unittest.mock import sentinel

import pytest

from lms.product.product import PluginConfig, Product


class FakePlugin:
    request: None

    @classmethod
    def from_request(cls, request):
        instance = cls()
        instance.request = request
        return instance


class TestProduct:
    def test_from_request(self, plugin_conf):
        @dataclass
        class MyProduct(Product):
            plugin_config = plugin_conf

        product = MyProduct.from_request(sentinel.request)

        for field in fields(PluginConfig):
            assert hasattr(product.plugin, field.name)
            plugin = getattr(product.plugin, field.name)
            assert isinstance(plugin, FakePlugin)
            assert plugin.request == sentinel.request

    @pytest.fixture
    def plugin_conf(self):
        return PluginConfig(
            **{field.name: FakePlugin for field in fields(PluginConfig)}
        )
