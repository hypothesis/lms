from enum import Enum

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

    def api_url(self, function: Function) -> str:
        url = f"{self._lms_url}/{self.API_PATH}?wstoken={self._token}&moodlewsrestformat=json"

        return url + f"&wsfunction={function.value}"

    def group_set_groups(self, course_id: int, group_set_id: int):
        url = self.api_url(Function.GET_GROUPINGS)
        url = f"{url}&groupingids[0]={group_set_id}&returngroups=1"
        response = self._http.post(url).json()

        return [
            {"id": g["id"], "name": g["name"], "group_set_id": group_set_id}
            for g in response[0]["groups"]
        ]

    def groups_for_user(self, course_id, group_set_id, user_id):
        url = self.api_url(Function.GET_USER_GROUPS)
        url = f"{url}&groupingid={group_set_id}&userid={user_id}&courseid={course_id}"
        print(url)
        response = self._http.post(url).json()

        return [
            {"id": g["id"], "name": g["name"], "group_set_id": group_set_id}
            for g in response["groups"]
        ]

    def course_group_sets(self, course_id: int) -> list[dict]:
        url = self.api_url(Function.GET_COURSE_GROUPINGS)
        response = self._http.post(url, params={"courseid": course_id}).json()

        return [{"id": g["id"], "name": g["name"]} for g in response]

    @classmethod
    def factory(cls, _context, request):
        return MoodleAPIClient(
            lms_url=request.lti_user.application_instance.lms_url,
            token="",
            http=request.find_service(name="http"),
        )
