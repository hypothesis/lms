from unittest.mock import patch, sentinel

import pytest

from lms.models import Grouping
from lms.product.plugin.grouping import GroupingPlugin
from tests import factories


class TestGroupingServicePlugin:
    def test_sections_enabled(self, plugin):
        assert not plugin.sections_enabled(
            sentinel.request, sentinel.application_instance, sentinel.course
        )

    def test_group_set_id_when_disabled(self, plugin):
        plugin.group_type = None

        assert not plugin.group_set_id(sentinel.request, sentinel.assignment)

    def test_group_set_id_when_no_assignment(self, plugin_with_groups):
        assert not plugin_with_groups.group_set_id(sentinel.request, None)

    def test_group_set_id_when_no_group_set(self, plugin):
        assignment = factories.Assignment(extra={})

        assert not plugin.group_set_id(sentinel.request, assignment)

    def test_group_set(self, plugin_with_groups):
        assignment = factories.Assignment(extra={"group_set_id": sentinel.id})

        assert (
            plugin_with_groups.group_set_id(sentinel.request, assignment) == sentinel.id
        )

    @pytest.mark.parametrize(
        "sections_enabled,group_set_id,expected",
        [
            (True, 1, Grouping.Type.GROUP),
            (True, None, Grouping.Type.SECTION),
            (False, 1, Grouping.Type.GROUP),
            (False, None, Grouping.Type.COURSE),
        ],
    )
    def test_launch_grouping_type(
        self, plugin, sections_enabled, group_set_id, expected
    ):
        with patch.object(
            plugin, "sections_enabled", return_value=sections_enabled
        ), patch.object(plugin, "group_set_id", return_value=group_set_id):
            assert (
                plugin.launch_grouping_type(
                    sentinel.request,
                    sentinel.application_instance,
                    sentinel.course,
                    sentinel.assignment,
                )
                == expected
            )

    @pytest.fixture
    def plugin(self):
        return GroupingPlugin()

    @pytest.fixture
    def plugin_with_groups(self, plugin):
        plugin.group_type = Grouping.Type.BLACKBOARD_GROUP
        return plugin
