from unittest.mock import sentinel

import pytest

from lms.product.blackboard._plugin.misc import BlackboardMiscPlugin


class TestBlackboardMiscPlugin:
    def test_accept_grading_comments(self, application_instance, plugin):
        assert not plugin.accept_grading_comments(application_instance)

    def test_factory(self, pyramid_request):
        plugin = BlackboardMiscPlugin.factory(sentinel.context, pyramid_request)
        assert isinstance(plugin, BlackboardMiscPlugin)

    @pytest.fixture
    def plugin(self):
        return BlackboardMiscPlugin()
