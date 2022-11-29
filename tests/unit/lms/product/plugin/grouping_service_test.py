from unittest.mock import sentinel

import pytest

from lms.models import Grouping
from lms.product.plugin.grouping import GroupingPlugin
from tests import factories


class TestGroupingServicePlugin:
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

    def test_get_group_set_id_when_disabled(self, plugin):
        plugin.group_type = None

        assert not plugin.get_group_set_id(sentinel.request, sentinel.assignment)

    def test_get_group_set_id_when_no_assignment(self, plugin_with_groups):
        assert not plugin_with_groups.get_group_set_id(sentinel.request, None)

    def test_get_group_set_id_when_no_group_set(self, plugin):
        assignment = factories.Assignment(extra={})

        assert not plugin.get_group_set_id(sentinel.request, assignment)

    def test_get_group_set_id(self, plugin_with_groups):
        assignment = factories.Assignment(extra={"group_set_id": sentinel.id})

        assert (
            plugin_with_groups.get_group_set_id(sentinel.request, assignment)
            == sentinel.id
        )

    @pytest.fixture
    def plugin(self):
        return GroupingPlugin()

    @pytest.fixture
    def plugin_with_groups(self, plugin):
        plugin.group_type = Grouping.Type.BLACKBOARD_GROUP
        return plugin
