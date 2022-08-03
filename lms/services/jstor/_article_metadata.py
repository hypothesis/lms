from html.parser import HTMLParser

from marshmallow import fields

from lms.validation import RequestsResponseSchema


class _ArticleMetadataSchema(RequestsResponseSchema):
    """
    Response schema for `/metadata/{doi}` endpoint in the JSTOR API.

    See https://labs.jstor.org/api/anno/docs
    """

    title = fields.Str()
    subtitle = fields.Str()

    reviewed_works = fields.List(fields.Str())
    """List of titles of works that this item is a review of."""

    has_pdf = fields.Boolean(required=True)
    """
    Does this item have a PDF?

    This can be false if the item is a collection (eg. of book chapters or
    journal articles).
    """

    requestor_access_level = fields.Str(required=True)
    """
    Does the current institution have access to the PDF?

    The "current" institution is the one identified by the site code specified
    in the Authorization header of the request.

    This will be "full_access" if the institution has access to the PDF,
    or another value (eg. "preview_access") otherwise.
    """


class ArticleMetadata:
    def __init__(self, data):
        self._data = data

    @classmethod
    def from_response(cls, response):
        return cls(_ArticleMetadataSchema(response).parse())

    def as_dict(self):
        return {"title": self.title, "content_status": self.content_status}

    @property
    def content_status(self) -> str:
        if not self._data["has_pdf"]:
            # Item does not have associated content (eg. a PDF)
            return "no_content"

        if self._data["requestor_access_level"] == "full_access":
            # Content is available for the item
            return "available"

        # This item has content, but the current institution does not have
        # access to it
        return "no_access"

    @property
    def title(self) -> str:
        # Reviews of other works may not have a title of their own, but we can
        # generate one from the reviewed work's metadata.
        if reviewed_works := self._data.get("reviewed_works"):
            title = f"Review: {reviewed_works[0]}"

        # Journal articles, book chapters and research reports have a title
        # field with a single entry.
        elif title := self._data.get("title"):

            # Some articles have a subtitle which needs to be appended for the
            # title to make sense.
            if subtitle := self._data.get("subtitle"):
                # Some titles include a trailing ':' delimiter, some do not.
                title = f"{title.rstrip(':')}: {subtitle}"

        else:
            title = "[Unknown title]"

        # Some titles contain HTML formatting tags, new lines or unwanted
        # extra spaces. Strip these to simplify downstream processing.
        return self._strip_html_tags(title)

    @staticmethod
    def _strip_html_tags(html: str) -> str:
        """Get plain text from a string which may contain HTML tags."""

        # Extract text nodes using HTMLParser. We rely on it being tolerant of
        # invalid markup.
        chunks = []
        parser = HTMLParser()
        parser.handle_data = chunks.append
        parser.feed(html)
        parser.close()

        # Strip leading/trailing whitespace and duplicate spaces
        return " ".join("".join(chunks).split())
