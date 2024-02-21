from unittest.mock import create_autospec, sentinel

import pytest

from lms.models import ApplicationInstance
from lms.services.moodle import MoodleAPIClient


class TestMoodleAPIClient:
    def test_course_group_sets(self, svc, http_service, group_sets):
        http_service.post.return_value.json.return_value = group_sets

        api_group_sets = svc.course_group_sets("COURSE_ID")

        http_service.post.assert_called_once_with(
            f"sentinel.lms_url/{svc.API_PATH}?wstoken=sentinel.token&moodlewsrestformat=json&wsfunction=core_group_get_course_groupings",
            params={"courseid": "COURSE_ID"},
        )
        assert api_group_sets == group_sets

    def test_group_set_groups(self, svc, http_service, groups):
        http_service.post.return_value.json.return_value = [{"groups": groups}]

        api_groups = svc.group_set_groups("GROUP_SET")

        http_service.post.assert_called_once_with(
            "sentinel.lms_url/webservice/rest/server.php?wstoken=sentinel.token&moodlewsrestformat=json&wsfunction=core_group_get_groupings&groupingids[0]=GROUP_SET&returngroups=1"
        )
        assert api_groups == [
            {"id": g["id"], "name": g["name"], "group_set_id": "GROUP_SET"}
            for g in groups
        ]

    def test_groups_for_user(self, svc, http_service, groups):
        http_service.post.return_value.json.return_value = {"groups": groups}

        api_groups = svc.groups_for_user("COURSE_ID", "GROUP_SET", "USER_ID")

        http_service.post.assert_called_once_with(
            "sentinel.lms_url/webservice/rest/server.php?wstoken=sentinel.token&moodlewsrestformat=json&wsfunction=core_group_get_course_user_groups&groupingid=GROUP_SET&userid=USER_ID&courseid=COURSE_ID"
        )
        assert api_groups == [
            {"id": g["id"], "name": g["name"], "group_set_id": "GROUP_SET"}
            for g in groups
        ]

    def test_factory(
        self,
        http_service,
        aes_service,
        pyramid_request,
    ):
        ai = create_autospec(ApplicationInstance)
        pyramid_request.lti_user.application_instance = ai

        service = MoodleAPIClient.factory(sentinel.context, pyramid_request)

        ai.settings.get_secret.assert_called_once_with(
            aes_service, "moodle", "api_token"
        )

        # pylint:disable=protected-access
        assert service._lms_url == ai.lms_url
        assert service._http == http_service
        assert service._token == ai.settings.get_secret.return_value

    @pytest.fixture
    def group_sets(self):
        return [
            {"id": 1, "name": "1"},
            {"id": 2, "name": "2"},
        ]

    @pytest.fixture
    def groups(self):
        return [
            {"id": 1, "name": "1"},
            {"id": 2, "name": "2"},
        ]

    @pytest.fixture
    def svc(self, http_service):
        return MoodleAPIClient(sentinel.lms_url, sentinel.token, http_service)
