from enum import Enum

from lms.services.aes import AESService
from lms.services.http import HTTPService


class Function(str, Enum):
    GET_SITE_INFO = "core_webservice_get_site_info"
    GET_COURSE_GROUPS = "core_group_get_course_groups"


class MoodleAPIClient:
    API_PATH = "webservice/rest/server.php"

    def __init__(self, lms_url: str, token: str, http: HTTPService) -> None:
        self._lms_url = lms_url
        self._token = token
        self._http = http

    def api_url(self, function: Function) -> str:
        url = f"{self._lms_url}/{self.API_PATH}?wstoken={self._token}&moodlewsrestformat=json"

        return url + f"&wsfunction={function.value}"

    def get_groups(self, course_id: int):
        url = self.api_url(Function.GET_COURSE_GROUPS)
        response = self._http.post(url, params={"courseid": course_id})
        return response.json()
