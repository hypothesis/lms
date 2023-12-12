from marshmallow import fields

from lms.services.html_service import strip_html_tags
from lms.validation import RequestsResponseSchema


class _ArticleMetadataSchema(RequestsResponseSchema):
    """
    Response schema for `/metadata/{doi}` endpoint in the JSTOR API.

    See https://labs.jstor.org/api/anno/docs
    """

    title = fields.Str()
    subtitle = fields.Str()

    # Ids of the related items
    next = fields.Str()
    previous = fields.Str()

    # Titles of the containing item
    book_title = fields.Str()
    book_subtitle = fields.Str()
    journal = fields.Str()

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
        return {
            "item": self.titles,
            "container": self.container,
            "content_status": self.content_status,
            "related_items": self.related_items,
        }

    @property
    def container(self):
        if titles := self._get_titles("book_title", "book_subtitle"):
            titles["type"] = "book"
            return titles

        if journal := self._data.get("journal"):
            return {"type": "journal", "title": self._strip_html_tags(journal)}

        return {"type": None, "title": None}

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
    def related_items(self):
        items = {}

        if next_id := self._data.get("next"):
            items["next_id"] = next_id

        if previous_id := self._data.get("previous"):
            items["previous_id"] = previous_id

        return items

    @property
    def titles(self) -> dict:
        # Reviews of other works may not have a title of their own, but we can
        # generate one from the reviewed work's metadata.
        if reviewed_works := self._data.get("reviewed_works"):
            return {"title": self._strip_html_tags(f"Review: {reviewed_works[0]}")}

        if titles := self._get_titles("title", "subtitle"):
            return titles

        return {"title": "[Unknown title]"}

    def _get_titles(self, title_key, subtitle_key):
        titles = {}

        # Journal articles, book chapters and research reports have a title
        # field with a single entry.
        if title := self._data.get(title_key):
            # Some titles have a colon on the end. We'll remove these, so we
            # can more easily format these without checking for it.
            titles["title"] = self._strip_html_tags(title).rstrip(": ")

            # Some articles have a subtitle which needs to be appended for the
            # title to make sense.
            if subtitle := self._data.get(subtitle_key):
                titles["subtitle"] = self._strip_html_tags(subtitle)

        return titles

    @staticmethod
    def _strip_html_tags(html: str) -> str:
        # Strip leading/trailing whitespace and duplicate spaces
        return " ".join(strip_html_tags(html).split())
