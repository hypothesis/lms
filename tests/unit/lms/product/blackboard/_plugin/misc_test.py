from unittest.mock import sentinel

import pytest

from lms.product.blackboard._plugin.misc import BlackboardMiscPlugin


class TestBlackboardMiscPlugin:
    def test_format_grading_comment_for_lms(self, plugin):
        assert plugin.format_grading_comment_for_lms("new\nline") == "new<br/>line"

    def test_factory(self, pyramid_request):
        plugin = BlackboardMiscPlugin.factory(sentinel.context, pyramid_request)
        assert isinstance(plugin, BlackboardMiscPlugin)

    @pytest.fixture
    def plugin(self):
        return BlackboardMiscPlugin()
