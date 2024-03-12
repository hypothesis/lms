from unittest.mock import sentinel

import pytest

from lms.models import Grouping
from lms.product.plugin.grouping import GroupingPlugin


class TestGroupingPlugin:
    @pytest.mark.parametrize(
        "sections_type,expected", [(None, False), (Grouping.Type.CANVAS_SECTION, True)]
    )
    def test_sections_enabled(self, plugin, sections_type, expected):
        plugin.sections_type = sections_type

        assert (
            plugin.sections_enabled(
                sentinel.request, sentinel.application_instance, sentinel.course
            )
            == expected
        )

    def test_get_group_set_id_when_disabled(self, misc_plugin, plugin, pyramid_request):
        group_set_id = plugin.get_group_set_id(
            pyramid_request, sentinel.assignment, sentinel.historical_assignment
        )

        misc_plugin.get_assignment_configuration.assert_called_once_with(
            pyramid_request, sentinel.assignment, sentinel.historical_assignment
        )
        assert (
            group_set_id
            == misc_plugin.get_assignment_configuration.return_value.get.return_value
        )

    @pytest.fixture
    def plugin(self):
        plugin = GroupingPlugin()
        plugin.group_type = Grouping.Type.BLACKBOARD_GROUP
        return plugin
