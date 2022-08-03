import pytest

from lms.views.api.jstor import JSTORAPIViews


@pytest.mark.usefixtures("jstor_service")
class TestJSTORAPIViews:
    def test_article_metadata(self, views, jstor_service, pyramid_request):
        pyramid_request.matchdict["article_id"] = "test-article"

        metadata = views.article_metadata()

        jstor_service.get_article_metadata.assert_called_once_with("test-article")
        assert metadata == jstor_service.get_article_metadata.return_value

    def test_article_thumbnail(self, views, jstor_service, pyramid_request):
        pyramid_request.matchdict["article_id"] = "test-article"

        thumbnail = views.article_thumbnail()

        jstor_service.thumbnail.assert_called_once_with("test-article")
        assert thumbnail == {"image": jstor_service.thumbnail.return_value}

    @pytest.fixture
    def views(self, pyramid_request):
        return JSTORAPIViews(pyramid_request)
