from enum import Enum

from lms.services.aes import AESService
from lms.services.http import HTTPService


class Function(str, Enum):
    GET_COURSE_GROUPINGS = "core_group_get_course_groupings"
    GET_GROUPINGS = "core_group_get_groupings"
    GET_USER_GROUPS = "core_group_get_course_user_groups"

    GET_COURSE_CONTENTS = "core_course_get_contents"

    GET_PAGES = "mod_page_get_pages_by_courses"


class MoodleAPIClient:
    API_PATH = "webservice/rest/server.php"

    def __init__(
        self, lms_url: str, token: str, http: HTTPService, file_service
    ) -> None:
        self._lms_url = lms_url
        self._token = token
        self._http = http
        self._file_service = file_service

    @property
    def token(self):  # pragma: no cover
        return self._token

    def group_set_groups(self, course_id: int, group_set_id: int) -> list[dict]:
        url = self._api_url(Function.GET_GROUPINGS)
        url = f"{url}&groupingids[0]={group_set_id}&returngroups=1"
        response = self._http.post(url).json()

        groups = response[0].get("groups", [])
        return [
            {"id": g["id"], "name": g["name"], "group_set_id": group_set_id}
            for g in groups
            # While the endpoint is not course based we filter by group on our
            # end to avoid using groups from one course in another.
            if g["courseid"] == course_id
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

        file_tree = self._construct_file_tree(course_id, files)
        self._file_service.upsert(
            list(
                self._documents_for_storage(
                    course_id,
                    file_tree,
                    folder_type="moodle_folder",
                    document_type="moodle_file",
                )
            )
        )
        return file_tree

    def page(self, course_id, page_id) -> dict | None:
        url = self._api_url(Function.GET_PAGES)
        url = f"{url}&courseids[0]={course_id}"
        pages = self._http.post(url).json()["pages"]
        pages = [page for page in pages if int(page["coursemodule"]) == int(page_id)]

        if not pages:
            return None
        page = pages[0]

        return {
            "id": page["id"],
            "course_module": page["coursemodule"],
            "title": page["name"],
            "body": page["content"],
        }

    def list_pages(self, course_id: int):
        contents = self.course_contents(course_id)
        root = {"type": "Folder", "display_name": "", "children": []}
        folders = {root["display_name"]: root}

        for topic in contents:
            topic_name = topic["name"]

            for module in topic["modules"]:
                current_node = root
                # Pages can only be at the top level modules
                if module["modname"] == "page":
                    if topic_name not in folders:
                        new_folder = {
                            "type": "Folder",
                            "display_name": topic_name,
                            "id": f"{course_id}-{topic_name}",
                            "lms_id": f"{course_id}-{topic_name}",
                            "children": [],
                        }
                        folders[topic_name] = new_folder
                        current_node["children"].append(new_folder)

                    current_node = folders[topic_name]

                    file_node = {
                        "type": "Page",
                        "display_name": module["name"],
                        "lms_id": module["id"],
                        "id": f"moodle://page/course/{course_id}/page_id/{module['id']}",
                    }
                    current_node["children"].append(file_node)

        self._file_service.upsert(
            list(
                self._documents_for_storage(
                    course_id,
                    root["children"],
                    folder_type="moodle_folder",
                    document_type="moodle_page",
                )
            )
        )
        return root["children"]

    @staticmethod
    def _get_contents(contents, parent=None):
        file_paths = []
        for content in contents:
            if content["mimetype"] != "application/pdf":
                continue
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
                "id": f"moodle://file/course/{course_id}/url/{file_data['url']}",
                "lms_id": file_data["url"],
                "updated_at": file_data["updated_at"],
            }
            current_node["children"].append(file_node)

        return root["children"]

    def _api_url(self, function: Function) -> str:
        url = f"{self._lms_url}/{self.API_PATH}?wstoken={self._token}&moodlewsrestformat=json"

        return url + f"&wsfunction={function.value}"

    def _documents_for_storage(  # pylint:disable=too-many-arguments
        self, course_id, files, folder_type, document_type, parent_id=None
    ):
        for file in files:
            yield {
                "type": folder_type if file["type"] == "Folder" else document_type,
                "course_id": course_id,
                "lms_id": file["lms_id"],
                "name": file["display_name"],
                "parent_lms_id": parent_id,
            }

            yield from self._documents_for_storage(
                course_id,
                file.get("children", []),
                folder_type,
                document_type,
                file["id"],
            )

    @classmethod
    def factory(cls, _context, request):
        application_instance = request.lti_user.application_instance
        return MoodleAPIClient(
            lms_url=application_instance.lms_url,
            token=application_instance.settings.get_secret(
                request.find_service(AESService), "moodle", "api_token"
            ),
            http=request.find_service(name="http"),
            file_service=request.find_service(name="file"),
        )
