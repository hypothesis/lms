from lms.api_client.generic_http.api import APIModel


class Attachment(APIModel):
    @property
    def filename(self):
        return self["filename"]

    @property
    def mime_type(self):
        return self["mimeType"]


class Content(APIModel):
    @property
    def title(self):
        return self["title"]

    @property
    def parent_id(self):
        return self.get("parentId")

    @staticmethod
    def _content_type(data):
        if not "contentHandler" in data:
            return None

        return data["contentHandler"]["id"]

    @classmethod
    def wrap(cls, api_getter, items):
        type_map = {subclass.bb_type: subclass for subclass in cls.__subclasses__()}

        return [
            type_map.get(cls._content_type(item), cls)(api_getter, item)
            for item in items
        ]


class BBFolder(Content):
    bb_type = "resource/x-bb-folder"

    @property
    def has_children(self):
        return self["hasChildren"]


class BBFile(Content):
    bb_type = "resource/x-bb-file"

    @property
    def filename(self):
        return self["contentHandler"]["file"]["fileName"]

    @property
    def extension(self):
        filename = self.filename
        if "." not in filename:
            return None

        return self.filename.rsplit(".", 1)[1].lower()
