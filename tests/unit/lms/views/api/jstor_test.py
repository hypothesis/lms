import pytest

from lms.views.api.jstor import JSTORAPIViews


@pytest.mark.usefixtures("jstor_service")
class TestJSTORAPIViews:
    def test_article_metadata(self, jstor_service, pyramid_request):
        views = JSTORAPIViews(pyramid_request)
        pyramid_request.matchdict["article_id"] = "test-article"

        metadata = views.article_metadata()

        jstor_service.metadata.assert_called_once_with("test-article")
        assert metadata == {
            "title": jstor_service.metadata.return_value["title"],
            "is_collection": False,
        }

    def test_article_thumbnail(self, jstor_service, pyramid_request):
        views = JSTORAPIViews(pyramid_request)
        pyramid_request.matchdict["article_id"] = "test-article"

        thumbnail = views.article_thumbnail()

        jstor_service.thumbnail.assert_called_once_with("test-article")
        assert thumbnail == {"image": jstor_service.thumbnail.return_value}
