from unittest.mock import sentinel

import pytest

from lms.product.plugin.launch import LaunchPlugin


class TestCanvasLaunchPlugin:
    @pytest.mark.parametrize("value,expected", [(None, False), (sentinel.url, True)])
    def test_is_assignment_gradable(self, plugin, value, expected):
        assert (
            plugin.is_assignment_gradable({"lis_outcome_service_url": value})
            == expected
        )

    def test_course_extra(self, plugin, pyramid_request):
        assert not plugin.course_extra(pyramid_request)

    @pytest.fixture
    def plugin(self):
        return LaunchPlugin()
