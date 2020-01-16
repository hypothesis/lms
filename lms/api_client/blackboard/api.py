from lms.api_client.generic_http.api_module import APIModule
from lms.api_client.generic_http.retriable import retriable


class APIRoot(APIModule):
    # API details: https://developer.blackboard.com/portal/displayApi

    def course(self, course_id):
        return self.extend(Course, course_id)

    def version(self):
        return self.call("GET", "system/version")


class Course(APIModule):
    def __init__(self, ws, parent, course_id):
        self.course_id = course_id

        super().__init__(ws, parent, f"/courses/{course_id}")

    @retriable
    def list_contents(self):
        return self.oauth2_call("GET", "contents")