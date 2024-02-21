from enum import Enum

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

    def get_course_contents(self, course_id: int) -> list[dict]:
        url = self.api_url(Function.GET_COURSE_CONTENTS)
        response = self._http.post(url, params={"courseid": course_id}).json()
        return response

    def list_files(self, course_id: int):
        contents = self.get_course_contents(course_id)

        from pprint import pprint

        files = []

        for topic in contents:
            topic_name = topic["name"]

            for module in topic["modules"]:
                if module["modname"] == "resource" and module["modplural"] == "Files":
                    files.extend(
                        self._get_contents(
                            module["contents"], course_id, parent=topic_name
                        )
                    )
                elif module["modname"] == "folder":
                    files.extend(
                        self._get_contents(
                            module["contents"],
                            course_id,
                            parent=topic_name + "/" + module["name"],
                        )
                    )
                else:
                    continue

        return self._construct_file_tree(course_id, files)

    @staticmethod
    def _get_contents(contents, course_id, parent=None):
        file_paths = []
        for content in contents:
            print(content["fileurl"])
            # TODO AVOID NON PDFS
            file_path = f"{parent}{content['filepath']}{content['filename']}"
            file_paths.append(
                {
                    "path": file_path,
                    "url": content["fileurl"],
                    "updated_at": content["timemodified"],
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
                        # TODO FULL PATH AS COMPONENT
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

    @classmethod
    def factory(cls, _context, request):
        return MoodleAPIClient(
            lms_url=request.lti_user.application_instance.lms_url,
            token="",
            http=request.find_service(name="http"),
        )
