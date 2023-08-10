from unittest.mock import patch, sentinel

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

    def test_get_document_default_behaviour(self, plugin, MiscPlugin):
        MiscPlugin.get_document_url.return_value = sentinel.url

        assert (
            plugin.get_document_url(
                sentinel.request, sentinel.assignment, sentinel.historical_assignment
            )
            == sentinel.url
        )

    def test_get_document_deep_linked_fallback(
        self, plugin, MiscPlugin, get_deep_linked_assignment_configuration
    ):
        MiscPlugin.get_document_url.return_value = None
        get_deep_linked_assignment_configuration.return_value = {"url": sentinel.url}

        assert (
            plugin.get_document_url(
                sentinel.request, sentinel.assignment, sentinel.historical_assignment
            )
            == sentinel.url
        )

    def test_get_document_returns_none(
        self, plugin, MiscPlugin, get_deep_linked_assignment_configuration
    ):
        MiscPlugin.get_document_url.return_value = None
        get_deep_linked_assignment_configuration.return_value = {}

        assert not plugin.get_document_url(
            sentinel.request, sentinel.assignment, sentinel.historical_assignment
        )

    def test_factory(self, pyramid_request):
        plugin = D2LMiscPlugin.factory(sentinel.context, pyramid_request)
        assert isinstance(plugin, D2LMiscPlugin)

    @pytest.fixture
    def plugin(self):
        return D2LMiscPlugin()

    @pytest.fixture
    def MiscPlugin(self):
        with patch("lms.product.d2l._plugin.misc.super") as patched:
            yield patched.return_value

    @pytest.fixture
    def get_deep_linked_assignment_configuration(self, plugin):
        with patch.object(
            plugin, "get_deep_linked_assignment_configuration", autospec=True
        ) as patched:
            yield patched
