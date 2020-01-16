# API details: https://developer.blackboard.com/portal/displayApi

import re

from lms.api_client.blackboard_classic.model import Attachment, Content
from lms.api_client.generic_http.api.module import APIModule
from lms.api_client.generic_http.retriable import retriable


def since(version):
    def deco(fn):
        fn.min_version = version
        return fn

    return deco


class APIRoot(APIModule):
    def course(self, course_id):
        return self.extend(CourseModule, course_id)

    @since("3000.3.0")
    def version(self):
        return self.call("GET", "system/version")["learn"]


class CourseModule(APIModule):
    UUID_PATTERN = re.compile("^[0-9a-f]{32}$")

    def __init__(self, ws, parent, course_id):
        if self.UUID_PATTERN.match(course_id):
            course_id = f"uuid:{course_id}"

        super().__init__(ws, parent, "/courses/{course_id}", {"course_id": course_id})

    @since("3000.1.0")
    @retriable
    def list_contents(self):
        return Content.wrap(self.content, self.call("GET", "contents")["results"])

    def content(self, content_id):
        return self.extend(CourseContentsModule, content_id)


class CourseContentsModule(APIModule):
    def __init__(self, ws, parent, content_id):
        super().__init__(
            ws, parent, "/contents/{content_id}", {"content_id": content_id}
        )

    @since("3000.1.0")
    @retriable
    def get(self):
        return Content(self.parent.content, self.call("GET", ""))

    @since("3000.1.0")
    @retriable
    def list_children(self):
        return Content.wrap(
            self.parent.content, self.call("GET", "children")["results"]
        )

    @since("3200.8.0")
    @retriable
    def list_attachments(self):
        return Attachment.wrap(
            self.attachment, self.call("GET", "attachments")["results"]
        )

    def attachment(self, attachment_id):
        return self.extend(AttachmentModule, attachment_id)

    def first_attachment(self):
        attachments = self.list_attachments()
        if len(attachments) != 1:
            raise ValueError("Expected a single attachment")

        return attachments[0]


class AttachmentModule(APIModule):
    def __init__(self, ws, parent, attachment_id):
        super().__init__(
            ws, parent, "/attachments/{attachment_id}", {"attachment_id": attachment_id}
        )

    @since("3200.8.0")
    @retriable
    def get(self):
        return Content(self.parent.attachment, self.call("GET", ""))

    @since("3200.8.0")
    def url(self):
        return self.path("download")

    @since("3200.8.0")
    @retriable
    def download(self):
        return self.call("GET", "download")

    @since("3200.8.0")
    @retriable
    def download_url(self):
        response = self.call("GET", "download", raw=True, allow_redirects=False)

        if response.status_code != 302:
            raise ValueError("Expected 302 redirect")

        return response.headers["Location"]
