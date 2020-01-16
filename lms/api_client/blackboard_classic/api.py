import re

from lms.api_client.generic_http.api_module import APIModule
from lms.api_client.generic_http.retriable import retriable


class BlackboardAPIModule(APIModule):
    UUID_PATTERN = re.compile("^[0-9a-f]{32}$")

    def decorate_uuid(self, _id):
        if self.UUID_PATTERN.match(_id):
            return f"uuid:{_id}"

        return _id


class APIRoot(BlackboardAPIModule):
    # API details: https://developer.blackboard.com/portal/displayApi

    def course(self, course_id):
        return self.extend(Course, course_id)

    def version(self):
        return self.call("GET", "system/version")


class Course(BlackboardAPIModule):
    def __init__(self, ws, parent, course_id):
        self.course_id = self.decorate_uuid(course_id)

        super().__init__(ws, parent, f"/courses/{self.course_id}")

    @retriable
    def list_contents(self):
        return self.oauth2_call("GET", "contents")
