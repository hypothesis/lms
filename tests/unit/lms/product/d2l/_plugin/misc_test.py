from unittest.mock import sentinel

import pytest

from lms.product.d2l._plugin.misc import D2LMiscPlugin


class TestD2LMiscPlugin:
    def test_deep_linking_prompt_for_title(self, plugin):
        assert plugin.deep_linking_prompt_for_title

    def test_get_ltia_aud_claim(self, plugin):
        assert (
            plugin.get_ltia_aud_claim(sentinel.registration)
            == "https://api.brightspace.com/auth/token"
        )

    def test_factory(self, pyramid_request):
        plugin = D2LMiscPlugin.factory(sentinel.context, pyramid_request)
        assert isinstance(plugin, D2LMiscPlugin)

    @pytest.fixture
    def plugin(self):
        return D2LMiscPlugin()
