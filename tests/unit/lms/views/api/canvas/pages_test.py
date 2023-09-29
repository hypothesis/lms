import pytest

from lms.services.canvas_api._pages import CanvasPage
from lms.views.api.canvas.pages import PagesAPIViews


@pytest.mark.usefixtures(
    "application_instance_service", "assignment_service", "canvas_service"
)
class TestPageAPIViews:
    def test_list_pages(self, canvas_service, pyramid_request, pages):
        course_id = "COURSE_ID"
        pyramid_request.matchdict = {"course_id": course_id}
        canvas_service.api.pages.list.return_value = pages

        result = PagesAPIViews(pyramid_request).list_pages()

        assert result == [
            {
                "id": f"canvas://page/course/{course_id}/page_id/{page.id}",
                "lms_id": page.id,
                "display_name": page.title,
                "type": "Page",
                "updated_at": page.updated_at,
            }
            for page in pages
        ]
        canvas_service.api.pages.list.assert_called_once_with(course_id)

    @pytest.fixture
    def pages(self):
        return [
            CanvasPage(id=i, title=f"title {i}", updated_at=f"updated {i}")
            for i in range(5)
        ]
