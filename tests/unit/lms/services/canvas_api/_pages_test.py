import pytest
from h_matchers import Any

from lms.services.canvas_api._pages import CanvasPage, CanvasPagesClient
from tests import factories


@pytest.mark.usefixtures("http_session", "oauth_token")
class TestCanvasPagesClient:
    def test_list(self, pages_client, http_session):
        pages = [
            {"page_id": 1, "title": "PAGE 1", "updated_at": "UPDATED_AT_1"},
            {"page_id": 2, "title": "PAGE 2", "updated_at": "UPDATED_AT_2"},
        ]
        http_session.send.return_value = factories.requests.Response(
            status_code=200, json_data=pages
        )

        response_pages = pages_client.list("COURSE_ID")

        self.assert_http_send(
            http_session,
            path="api/v1/courses/COURSE_ID/pages",
            query={"published": "1", "per_page": "1000"},
        )
        assert response_pages == [
            CanvasPage(
                id=page["page_id"], title=page["title"], updated_at=page["updated_at"]
            )
            for page in pages
        ]

    def test_page(self, pages_client, http_session):
        page = {
            "page_id": 1,
            "title": "PAGE 1",
            "updated_at": "UPDATED_AT_1",
            "body": "SOME HTML",
        }
        http_session.send.return_value = factories.requests.Response(
            status_code=200, json_data=page
        )

        response_page = pages_client.page("COURSE_ID", "PAGE_ID")

        self.assert_http_send(
            http_session,
            path="api/v1/courses/COURSE_ID/pages/PAGE_ID",
        )
        assert response_page == CanvasPage(
            id=page["page_id"],
            title=page["title"],
            updated_at=page["updated_at"],
            body=page["body"],
        )

    def assert_http_send(
        self, http_session, path, method="GET", query=None, timeout=(10, 10)
    ):
        http_session.send.assert_called_once_with(
            Any.request(method, url=Any.url.with_path(path).with_query(query)),
            timeout=timeout,
        )

    @pytest.fixture
    def pages_client(self, authenticated_client):
        return CanvasPagesClient(authenticated_client)
