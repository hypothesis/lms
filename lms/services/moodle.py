from enum import Enum

from lms.services.aes import AESService
from lms.services.http import HTTPService


class Function(str, Enum):
    GET_COURSE_GROUPINGS = "core_group_get_course_groupings"
    GET_GROUPINGS = "core_group_get_groupings"
    GET_USER_GROUPS = "core_group_get_course_user_groups"

    GET_COURSE_CONTENTS = "core_course_get_contents"


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

    def course_contents(self, course_id: int) -> list[dict]:
        url = self._api_url(Function.GET_COURSE_CONTENTS)
        response = self._http.post(url, params={"courseid": course_id}).json()
        return response

    def list_files(self, course_id: int):
        contents = self.course_contents(course_id)
        files = []

        for topic in contents:
            topic_name = topic["name"]

            for module in topic["modules"]:
                # Files can be at the top level modules
                if module["modname"] == "resource" and module["modplural"] == "Files":
                    files.extend(
                        self._get_contents(module["contents"], parent=topic_name)
                    )

                # Or nested inside folders
                elif module["modname"] == "folder":
                    files.extend(
                        self._get_contents(
                            module["contents"], parent=topic_name + "/" + module["name"]
                        )
                    )
                else:
                    continue

        return self._construct_file_tree(course_id, files)

    @staticmethod
    def _get_contents(contents, parent=None):
        file_paths = []
        for content in contents:
            file_path = f"{parent}{content['filepath']}{content['filename']}"
            file_paths.append(
                {
                    "path": file_path,
                    "url": content["fileurl"],
                    "updated_at": content["timemodified"] * 1000,
                }
            )

        return file_paths

    @staticmethod
    def _construct_file_tree(course_id, files):
        root = {"type": "Folder", "display_name": "", "children": []}
        folders = {root["display_name"]: root}

        for file_data in files:
            path_components = file_data["path"].split("/")
            current_node = root

            for component in path_components[:-1]:
                if component not in folders:
                    new_folder = {
                        "type": "Folder",
                        "display_name": component,
                        "id": f"{course_id}-{component}",
                        "lms_id": f"{course_id}-{component}",
                        "children": [],
                    }
                    folders[component] = new_folder
                    current_node["children"].append(new_folder)
                current_node = folders[component]

            file_node = {
                "type": "File",
                "display_name": path_components[-1],
                "id": f"moodle://file/url/{file_data['url']}",
                "lms_id": f"moodle://file/url/{file_data['url']}",
                "updated_at": file_data["updated_at"],
            }
            current_node["children"].append(file_node)

        return root["children"]

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
