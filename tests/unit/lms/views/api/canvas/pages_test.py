from unittest.mock import sentinel

import pytest
from h_matchers import Any

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

    def test_via_url(
        self,
        helpers,
        pyramid_request,
        application_instance,
        assignment_service,
        lti_user,
        BearerTokenSchema,
    ):
        pyramid_request.matchdict["resource_link_id"] = sentinel.resource_link_id
        assignment_service.get_assignment.return_value.document_url = "DOCUMENT_URL"
        BearerTokenSchema.return_value.authorization_param.return_value = "TOKEN"

        response = PagesAPIViews(pyramid_request).via_url()

        assignment_service.get_assignment.assert_called_once_with(
            application_instance.tool_consumer_instance_guid,
            sentinel.resource_link_id,
        )
        BearerTokenSchema.assert_called_once_with(pyramid_request)
        BearerTokenSchema.return_value.authorization_param.assert_called_once_with(
            lti_user
        )
        helpers.via_url.assert_called_once_with(
            pyramid_request,
            Any.url.with_path("/api/canvas/pages/proxy").with_query(
                {
                    "document_url": "DOCUMENT_URL",
                    "authorization": "TOKEN",
                }
            ),
        )
        assert response == {"via_url": helpers.via_url.return_value}

    def test_proxy(self, canvas_service, pyramid_request):
        pyramid_request.params[
            "document_url"
        ] = "canvas://page/course/COURSE_ID/page_id/PAGE_ID"
        canvas_service.api.pages.page.return_value = CanvasPage(
            id=1, title=sentinel.title, updated_at="updated", body=sentinel.body
        )

        response = PagesAPIViews(pyramid_request).proxy()

        canvas_service.api.pages.page.assert_called_once_with("COURSE_ID", "PAGE_ID")
        assert response == {"title": sentinel.title, "body": sentinel.body}

    @pytest.fixture
    def pages(self):
        return [
            CanvasPage(id=i, title=f"title {i}", updated_at=f"updated {i}")
            for i in range(5)
        ]

    @pytest.fixture
    def helpers(self, patch):
        return patch("lms.views.api.canvas.pages.helpers")

    @pytest.fixture
    def BearerTokenSchema(self, patch):
        return patch("lms.views.api.canvas.pages.BearerTokenSchema")
