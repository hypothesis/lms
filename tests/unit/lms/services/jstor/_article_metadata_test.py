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
                "has_pdf": True,
                "requestor_access_level": "full_access",
            }
        )

        data = ArticleMetadata.from_response(response).as_dict()

        assert data == {"content_status": "available", "title": "Title"}

    @pytest.mark.parametrize(
        "response",
        [
            {
                "title": ["This should be a string"],
                "has_pdf": True,
                "requestor_access_level": "full_access",
            },
            {"title": "Test with missing fields"},
        ],
    )
    def test_from_request_with_bad_responses(self, response):
        with pytest.raises(ExternalRequestError) as exc:
            ArticleMetadata.from_response(
                factories.requests.Response(json_data=response)
            )

        assert exc.value.validation_errors is not None

    @pytest.mark.parametrize(
        "response, expected_title",
        [
            # Simple title
            ({"title": ""}, "[Unknown title]"),
            ({"title": "SIMPLE"}, "SIMPLE"),
            ({"title": "SIMPLE", "subtitle": ""}, "SIMPLE"),
            ({"title": "SIMPLE", "subtitle": "SUBTITLE"}, "SIMPLE: SUBTITLE"),
            ({"title": "SIMPLE:", "subtitle": "SUBTITLE"}, "SIMPLE: SUBTITLE"),
            # Article that is a review of another work
            # These have null "tb" and "tbsub" fields, which should be ignored
            (
                {"title": "Ignored", "reviewed_works": ["Reviewed work"]},
                "Review: Reviewed work",
            ),
            # Titles with extra whitespace, new lines or HTML should be cleaned up.
            ({"title": "   A \n B   \t   C  "}, "A B C"),
            ({"title": "A <em>B</em>", "subtitle": "C <em>D</em> E"}, "A B: C D E"),
            ({"title": "A<b>B"}, "AB"),
            # This isn't a tag!
            ({"title": "A<B"}, "A<B"),
        ],
    )
    def test_title(self, response, expected_title):
        assert ArticleMetadata(response).title == expected_title

    @pytest.mark.parametrize(
        "has_pdf, access_level, expected_status",
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
