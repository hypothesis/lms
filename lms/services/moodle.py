from enum import Enum

from lms.services.aes import AESService
from lms.services.http import HTTPService


class Function(str, Enum):
    GET_COURSE_GROUPINGS = "core_group_get_course_groupings"
    GET_GROUPINGS = "core_group_get_groupings"
    GET_USER_GROUPS = "core_group_get_course_user_groups"


class MoodleAPIClient:
    API_PATH = "webservice/rest/server.php"

    def __init__(self, lms_url: str, token: str, http: HTTPService) -> None:
        self._lms_url = lms_url
        self._token = token
        self._http = http

    def group_set_groups(self, group_set_id: int) -> list[dict]:
        url = self._api_url(Function.GET_GROUPINGS)
        url = f"{url}&groupingids[0]={group_set_id}&returngroups=1"
        response = self._http.post(url).json()

        groups = response[0].get("groups", [])
        return [
            {"id": g["id"], "name": g["name"], "group_set_id": group_set_id}
            for g in groups
        ]

    def groups_for_user(self, course_id, group_set_id, user_id):
        url = self._api_url(Function.GET_USER_GROUPS)
        url = f"{url}&groupingid={group_set_id}&userid={user_id}&courseid={course_id}"
        response = self._http.post(url).json()

        return [
            {"id": g["id"], "name": g["name"], "group_set_id": group_set_id}
            for g in response["groups"]
        ]

    def course_group_sets(self, course_id: int) -> list[dict]:
        url = self._api_url(Function.GET_COURSE_GROUPINGS)
        response = self._http.post(url, params={"courseid": course_id}).json()

        return [{"id": g["id"], "name": g["name"]} for g in response]

    def _api_url(self, function: Function) -> str:
        url = f"{self._lms_url}/{self.API_PATH}?wstoken={self._token}&moodlewsrestformat=json"

        return url + f"&wsfunction={function.value}"

    @classmethod
    def factory(cls, _context, request):
        application_instance = request.lti_user.application_instance
        return MoodleAPIClient(
            lms_url=application_instance.lms_url,
            token=application_instance.settings.get_secret(
                request.find_service(AESService), "moodle", "api_token"
            ),
            http=request.find_service(name="http"),
        )
