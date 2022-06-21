from unittest.mock import sentinel

import pytest

from lms.views.api.canvas.sync import Sync
from tests import factories
from tests.conftest import TEST_SETTINGS


@pytest.mark.usefixtures(
    "application_instance_service", "lti_h_service", "course_service"
)
class TestSync:
    @pytest.mark.usefixtures("is_speedgrader")
    def test_sync_when_sections(
        self, lti_h_service, grouping_service, lti_user, course_service, pyramid_request
    ):
        sections = factories.CanvasSection.create_batch(5)
        grouping_service.get_sections.return_value = sections

        groupids = Sync(pyramid_request).sync()

        course_service.get_by_context_id.assert_called_once_with(sentinel.context_id)
        grouping_service.get_sections.assert_called_once_with(
            sentinel.user,
            lti_user,
            course_service.get_by_context_id.return_value,
            sentinel.canvas_user_id,
        )
        lti_h_service.sync.assert_called_once_with(
            grouping_service.get_sections.return_value, sentinel.group_info
        )

        assert groupids == [
            section.groupid(TEST_SETTINGS["h_authority"]) for section in sections
        ]

    @pytest.mark.usefixtures("with_invalid_group_set")
    def test_sync_sections_fallback_invalid_group_set(
        self, pyramid_request, grouping_service
    ):
        Sync(pyramid_request).sync()

        grouping_service.get_sections.assert_called_once()

    @pytest.mark.usefixtures("is_group_launch")
    def test_sync_when_groups(
        self,
        lti_h_service,
        grouping_service,
        lti_user,
        course_service,
        pyramid_request,
    ):
        groups = factories.CanvasGroup.create_batch(5)
        grouping_service.get_groups.return_value = groups

        groupids = Sync(pyramid_request).sync()

        course_service.get_by_context_id.assert_called_once_with(sentinel.context_id)
        grouping_service.get_groups.assert_called_once_with(
            sentinel.user,
            lti_user,
            course_service.get_by_context_id.return_value,
            1,
            None,
        )
        lti_h_service.sync.assert_called_once_with(
            grouping_service.get_groups.return_value, sentinel.group_info
        )
        assert groupids == [
            group.groupid(TEST_SETTINGS["h_authority"]) for group in groups
        ]

    @pytest.mark.usefixtures("is_groups_and_speed_grader")
    def test_sync_when_groups_and_speed_grader(
        self,
        grouping_service,
        lti_user,
        course_service,
        pyramid_request,
    ):
        Sync(pyramid_request).sync()

        grouping_service.get_groups.assert_called_once_with(
            sentinel.user,
            lti_user,
            course_service.get_by_context_id.return_value,
            100,
            sentinel.canvas_user_id,
        )

    @pytest.fixture
    def with_invalid_group_set(self, application_instance_service, request_json):
        application_instance_service.get_current.return_value.settings = {
            "canvas": {"groups_enabled": True}
        }
        request_json["course"]["group_set"] = "INVALID"

    @pytest.fixture
    def is_group_launch(self, application_instance_service, request_json):
        request_json["course"]["group_set"] = 1
        application_instance_service.get_current.return_value.settings = {
            "canvas": {"groups_enabled": True}
        }

    @pytest.fixture
    def is_groups_and_speed_grader(self, application_instance_service, request_json):
        request_json["learner"] = {"canvas_user_id": sentinel.canvas_user_id}
        application_instance_service.get_current.return_value.settings = {
            "canvas": {"groups_enabled": True}
        }
        request_json["learner"]["group_set"] = 100

    @pytest.fixture
    def is_speedgrader(self, request_json):
        request_json["learner"] = {"canvas_user_id": sentinel.canvas_user_id}

    @pytest.fixture
    def pyramid_request(self, pyramid_request, request_json):
        pyramid_request.json = request_json
        pyramid_request.user = sentinel.user
        return pyramid_request

    @pytest.fixture
    def request_json(self):
        return {
            "course": {"context_id": sentinel.context_id},
            "group_info": sentinel.group_info,
        }
