from enum import Enum

from lms.services.http import HTTPService


class Function(str, Enum):
    GET_COURSE_GROUPS = "core_group_get_course_groups"

    GET_COURSE_GROUPINGS = "core_group_get_course_groupings"
    """[{'id': 2, 'courseid': 11, 'name': 'Grouping in course', 'description': '', 'descriptionformat': 0, 'idnumber': ''}]"""

    GET_GROUPINGS_DETAILS = "core_group_get_groupings"


class MoodleAPIClient:
    API_PATH = "webservice/rest/server.php"

    COURSE_GROUP_SET_ID = "#COURSE"
    """Moodle allows to create groups that don't belong to a group set, we'll fake group set id to handle them as one in our end."""

    def __init__(self, lms_url: str, token: str, http: HTTPService) -> None:
        self._lms_url = lms_url
        self._token = token
        self._http = http

    def api_url(self, function: Function) -> str:
        url = f"{self._lms_url}/{self.API_PATH}?wstoken={self._token}&moodlewsrestformat=json"

        return url + f"&wsfunction={function.value}"

    def course_groups(self, course_id: int):
        url = self.api_url(Function.GET_COURSE_GROUPS)
        response = self._http.post(url, params={"courseid": course_id})
        return response.json()

    def course_group_sets(self, course_id: int) -> dict:
        groups_sets_response = self._http.post(url, params={"courseid": course_id}).json()

        group_set_ids = [group_set['id'] for group_set in groups_sets_response]


    @classmethod
    def factory(cls, _context, request):
        return MoodleAPIClient(
            lms_url=request.lti_user.application_instance.lms_url,
            token = "",
            http=request.find_service(name="http"),
        )
