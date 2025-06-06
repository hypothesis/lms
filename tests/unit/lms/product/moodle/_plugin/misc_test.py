from unittest.mock import patch, sentinel

import pytest

from lms.product.moodle._plugin.misc import MoodleMiscPlugin
from tests import factories


class TestMoodlePlugin:
    def test_prompt_for_gradable_returns_false_for_lti_1p0(
        self, application_instance, plugin
    ):
        assert plugin.deep_linking_prompt_for_gradable(application_instance) is False

    @pytest.mark.parametrize("feature_flag", [True, False])
    def test_prompt_for_gradable_returns_setting_for_lti_13(
        self, lti_v13_application_instance, feature_flag, plugin
    ):
        lti_v13_application_instance.settings.set(
            "hypothesis", "prompt_for_gradable", feature_flag
        )

        assert (
            plugin.deep_linking_prompt_for_gradable(lti_v13_application_instance)
            == feature_flag
        )

    def test_get_assignment_configuration_outdated_db_info(
        self, plugin, pyramid_request, get_deep_linked_assignment_configuration
    ):
        assignment = factories.Assignment(
            document_url=sentinel.db_document_url,
            extra={"group_set_id": sentinel.db_group_set_id},
            deep_linking_uuid=sentinel.old_dl_uuid,
        )
        get_deep_linked_assignment_configuration.return_value = {
            "url": sentinel.dl_document_url,
            "group_set": sentinel.dl_group_set_id,
            "deep_linking_uuid": sentinel.new_dl_uuid,
        }

        result = plugin.get_assignment_configuration(
            pyramid_request, assignment, sentinel.historical_assignment
        )

        assert result == {
            "document_url": sentinel.dl_document_url,
            "group_set_id": sentinel.dl_group_set_id,
        }
        assert assignment.deep_linking_uuid == sentinel.new_dl_uuid

    def test_get_assignment_configuration_with_assignment_in_db_existing_assignment(
        self, plugin, pyramid_request
    ):
        assignment = factories.Assignment(
            document_url=sentinel.document_url,
            extra={"group_set_id": sentinel.group_set_id},
        )

        result = plugin.get_assignment_configuration(
            pyramid_request, assignment, sentinel.historical_assignment
        )

        assert result == {
            "document_url": sentinel.document_url,
            "group_set_id": sentinel.group_set_id,
        }

    def test_get_assignment_configuration_with_assignment_in_db_new_deep_link(
        self, plugin, pyramid_request, get_deep_linked_assignment_configuration
    ):
        assignment = factories.Assignment(
            document_url=sentinel.document_url,
            deep_linking_uuid=None,
            extra={"group_set_id": sentinel.group_set_id},
        )

        get_deep_linked_assignment_configuration.return_value = {
            "url": sentinel.dl_document_url,
            "group_set": sentinel.dl_group_set_id,
            "deep_linking_uuid": sentinel.new_dl_uuid,
        }

        result = plugin.get_assignment_configuration(
            pyramid_request, assignment, sentinel.historical_assignment
        )
        assert result == {
            "document_url": sentinel.dl_document_url,
            "group_set_id": sentinel.dl_group_set_id,
        }
        assert assignment.deep_linking_uuid == sentinel.new_dl_uuid

    def test_get_assignment_configuration_deep_linked_fallback(
        self, plugin, get_deep_linked_assignment_configuration
    ):
        get_deep_linked_assignment_configuration.return_value = {
            "url": sentinel.url,
            "group_set": sentinel.group_set_id,
        }

        result = plugin.get_assignment_configuration(sentinel.request, None, None)

        assert result == {
            "document_url": sentinel.url,
            "group_set_id": sentinel.group_set_id,
        }

    @pytest.fixture
    def plugin(self):
        return MoodleMiscPlugin()

    @pytest.fixture
    def get_deep_linked_assignment_configuration(self, plugin):
        with patch.object(
            plugin, "get_deep_linked_assignment_configuration", autospec=True
        ) as patched:
            yield patched
