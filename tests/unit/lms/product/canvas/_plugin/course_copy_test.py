from unittest.mock import sentinel

import pytest

from lms.product.canvas import CanvasCourseCopyPlugin


class TestCanvasCourseCopyPlugin:
    def test_find_matching_group_set_in_course(self, plugin):
        assert not plugin.find_matching_group_set_in_course(
            sentinel.course, sentinel.group_set_id
        )

    def test_factory(self, pyramid_request):
        plugin = CanvasCourseCopyPlugin.factory(sentinel.context, pyramid_request)

        assert isinstance(plugin, CanvasCourseCopyPlugin)

    @pytest.fixture
    def plugin(self):
        return CanvasCourseCopyPlugin()
