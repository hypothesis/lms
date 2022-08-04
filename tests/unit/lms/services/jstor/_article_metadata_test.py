import pytest

from lms.services import ExternalRequestError
from lms.services.jstor._article_metadata import ArticleMetadata
from tests import factories


class TestArticleMetadata:
    def test_it(self):
        # This is a full happy path test
        response = factories.requests.Response(
            json_data={
                "title": "Title",
                "subtitle": "Subtitle",
                "has_pdf": True,
                "requestor_access_level": "full_access",
            }
        )

        data = ArticleMetadata.from_response(response).as_dict()

        assert data == {
            "item": {"title": "Title", "subtitle": "Subtitle"},
            "content_status": "available",
        }

    def test_from_request_with_bad_response(self):
        with pytest.raises(ExternalRequestError):
            ArticleMetadata.from_response(
                factories.requests.Response(json_data={"not": "valid"})
            )

    @pytest.mark.parametrize(
        "response,expected_titles",
        [
            # Simple title
            ({}, {"title": "[Unknown title]"}),
            ({"title": ""}, {"title": "[Unknown title]"}),
            ({"title": "SIMPLE"}, {"title": "SIMPLE"}),
            ({"title": " <b>COLON :</b> "}, {"title": "COLON"}),
            ({"title": "SIMPLE", "subtitle": ""}, {"title": "SIMPLE"}),
            (
                {"title": "SIMPLE", "subtitle": "SUBTITLE"},
                {"title": "SIMPLE", "subtitle": "SUBTITLE"},
            ),
            # Article that is a review of another work
            (
                {"title": "Ignored", "reviewed_works": ["Reviewed work"]},
                {"title": "Review: Reviewed work"},
            ),
            # Extra whitespace, new lines or HTML should be cleaned up
            (
                {"title": " A <em>B</em>", "subtitle": " C <em>D</em> E"},
                {"title": "A B", "subtitle": "C D E"},
            ),
            # This isn't a tag!
            ({"title": "A<B"}, {"title": "A<B"}),
        ],
    )
    def test_titles(self, response, expected_titles):
        assert ArticleMetadata(response).titles == expected_titles

    @pytest.mark.parametrize(
        "has_pdf,access_level,expected_status",
        [
            (True, "full_access", "available"),
            (False, "full_access", "no_content"),
            (True, "preview_access", "no_access"),
        ],
    )
    def test_get_article_metadata_returns_content_status(
        self, has_pdf, access_level, expected_status
    ):
        meta = ArticleMetadata(
            {"has_pdf": has_pdf, "requestor_access_level": access_level}
        )

        assert meta.content_status == expected_status
