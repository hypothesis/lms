from unittest.mock import sentinel

import pytest

from lms.models import Grouping
from lms.product.plugin.grouping import GroupingPlugin
from tests import factories


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

    def test_get_group_set_id_when_disabled(
        self, plugin_without_groups, pyramid_request
    ):
        assert not plugin_without_groups.get_group_set_id(
            pyramid_request, sentinel.assignment
        )

    @pytest.mark.usefixtures("with_non_deep_linked_group_set")
    def test_get_group_set_id_when_no_assignment(self, plugin, pyramid_request):
        assert not plugin.get_group_set_id(pyramid_request, None)

    def test_get_group_set_id_when_no_group_set(self, plugin, pyramid_request):
        assignment = factories.Assignment(extra={})

        assert not plugin.get_group_set_id(pyramid_request, assignment, None)

    def test_get_group_set_id_from_historical_assignment(self, plugin, pyramid_request):
        historical_assignment = factories.Assignment(
            extra={"group_set_id": sentinel.id}
        )

        assert (
            plugin.get_group_set_id(pyramid_request, None, historical_assignment)
            == sentinel.id
        )

    def test_get_group_set_id(self, plugin, pyramid_request):
        assignment = factories.Assignment(extra={"group_set_id": sentinel.id})

        assert plugin.get_group_set_id(pyramid_request, assignment) == sentinel.id

    @pytest.mark.usefixtures("with_deep_linked_group_set")
    def test_get_group_set_id_from_deep_linking(self, plugin, pyramid_request):
        assert (
            plugin.get_group_set_id(pyramid_request, None, None)
            == sentinel.deep_linked_id
        )

    @pytest.fixture
    def with_deep_linked_group_set(self, misc_plugin):
        misc_plugin.get_deep_linked_assignment_configuration.return_value = {
            "group_set": sentinel.deep_linked_id
        }

    @pytest.fixture
    def with_non_deep_linked_group_set(self, misc_plugin):
        misc_plugin.get_deep_linked_assignment_configuration.return_value = {}

    @pytest.fixture
    def plugin(self):
        plugin = GroupingPlugin()
        plugin.group_type = Grouping.Type.BLACKBOARD_GROUP
        return plugin

    @pytest.fixture
    def plugin_without_groups(self, plugin):
        plugin.group_type = None
        return plugin
