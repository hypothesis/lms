import random
from unittest.mock import Mock, sentinel

import pytest
from h_matchers import Any

from lms.services.canvas_api._pages import CanvasPage
from lms.services.exceptions import CanvasAPIError
from lms.views.api.canvas.pages import PageNotFoundInCourse, PagesAPIViews


@pytest.mark.usefixtures(
    "application_instance_service", "assignment_service", "canvas_service"
)
class TestPageAPIViews:
    def test_list_pages(self, canvas_service, pyramid_request, pages):
        course_id = "COURSE_ID"
        pyramid_request.matchdict = {"course_id": course_id}
        canvas_service.api.pages.list.return_value = pages

        result = PagesAPIViews(pyramid_request).list_pages()

        assert result == sorted(
            [
                {
                    "id": f"canvas://page/course/{course_id}/page_id/{page.id}",
                    "lms_id": page.id,
                    "display_name": page.title,
                    "mime_type": "text/html",
                    "type": "File",
                    "updated_at": page.updated_at,
                }
                for page in pages
            ],
            key=lambda p: p["display_name"].lower(),
        )
        canvas_service.api.pages.list.assert_called_once_with(course_id)

    @pytest.mark.usefixtures("course_copy_plugin")
    def test_via_url(
        self,
        helpers,
        pyramid_request,
        application_instance,
        assignment_service,
        lti_user,
        BearerTokenSchema,
        course_service,
    ):
        assignment_service.get_assignment.return_value.document_url = (
            "canvas://page/course/COURSE_ID/page_id/PAGE_ID"
        )
        course_service.get_by_context_id.return_value.extra = {
            "canvas": {"custom_canvas_course_id": "COURSE_ID"}
        }
        BearerTokenSchema.return_value.authorization_param.return_value = "TOKEN"

        response = PagesAPIViews(pyramid_request).via_url()

        assignment_service.get_assignment.assert_called_once_with(
            application_instance.tool_consumer_instance_guid, lti_user.lti.assignment_id
        )
        BearerTokenSchema.assert_called_once_with(pyramid_request)
        BearerTokenSchema.return_value.authorization_param.assert_called_once_with(
            lti_user
        )
        helpers.via_url.assert_called_once_with(
            pyramid_request,
            Any.url.with_path("/api/canvas/pages/proxy").with_query(
                {
                    "course_id": "COURSE_ID",
                    "page_id": "PAGE_ID",
                    "authorization": "TOKEN",
                }
            ),
            options={"via.proxy_frames": "0"},
        )
        assert response == {"via_url": helpers.via_url.return_value}

    @pytest.mark.usefixtures("course_copy_plugin")
    def test_via_url_copied_with_mapped_id(
        self,
        helpers,
        pyramid_request,
        assignment_service,
        BearerTokenSchema,
        course_service,
    ):
        assignment_service.get_assignment.return_value.document_url = (
            "canvas://page/course/COURSE_ID/page_id/PAGE_ID"
        )
        course_service.get_by_context_id.return_value.extra = {
            "canvas": {"custom_canvas_course_id": "OTHER_COURSE_ID"}
        }
        course_service.get_by_context_id.return_value.get_mapped_page_id.return_value = (
            "OTHER_PAGE_ID"
        )
        BearerTokenSchema.return_value.authorization_param.return_value = "TOKEN"

        response = PagesAPIViews(pyramid_request).via_url()

        helpers.via_url.assert_called_once_with(
            pyramid_request,
            Any.url.with_path("/api/canvas/pages/proxy").with_query(
                {
                    "course_id": "OTHER_COURSE_ID",
                    "page_id": "OTHER_PAGE_ID",
                    "authorization": "TOKEN",
                }
            ),
            options={"via.proxy_frames": "0"},
        )
        assert response == {"via_url": helpers.via_url.return_value}

    def test_via_url_copied_no_page_found(
        self,
        pyramid_request,
        assignment_service,
        course_service,
        course_copy_plugin,
    ):
        assignment_service.get_assignment.return_value.document_url = (
            "canvas://page/course/COURSE_ID/page_id/PAGE_ID"
        )
        course_service.get_by_context_id.return_value.extra = {
            "canvas": {"custom_canvas_course_id": "OTHER_COURSE_ID"}
        }
        course_service.get_by_context_id.return_value.get_mapped_page_id.return_value = (
            None
        )
        course_copy_plugin.find_matching_page_in_course.return_value = None

        with pytest.raises(PageNotFoundInCourse):
            PagesAPIViews(pyramid_request).via_url()

        course_copy_plugin.find_matching_page_in_course.assert_called_once_with(
            "PAGE_ID", "OTHER_COURSE_ID"
        )

    def test_via_url_copied_found_page(
        self,
        pyramid_request,
        assignment_service,
        course_service,
        course_copy_plugin,
        BearerTokenSchema,
        helpers,
    ):
        assignment_service.get_assignment.return_value.document_url = (
            "canvas://page/course/COURSE_ID/page_id/PAGE_ID"
        )
        course_service.get_by_context_id.return_value.extra = {
            "canvas": {"custom_canvas_course_id": "OTHER_COURSE_ID"}
        }
        course_service.get_by_context_id.return_value.get_mapped_page_id.return_value = (
            None
        )
        BearerTokenSchema.return_value.authorization_param.return_value = "TOKEN"

        course_copy_plugin.find_matching_page_in_course.return_value = Mock(
            lms_id="OTHER_PAGE_ID"
        )

        response = PagesAPIViews(pyramid_request).via_url()

        course_copy_plugin.find_matching_page_in_course.assert_called_once_with(
            "PAGE_ID", "OTHER_COURSE_ID"
        )
        course_service.get_by_context_id.return_value.set_mapped_page_id(
            "PAGE_ID", "OTHER_PAGE_ID"
        )

        helpers.via_url.assert_called_once_with(
            pyramid_request,
            Any.url.with_path("/api/canvas/pages/proxy").with_query(
                {
                    "course_id": "OTHER_COURSE_ID",
                    "page_id": "OTHER_PAGE_ID",
                    "authorization": "TOKEN",
                }
            ),
            options={"via.proxy_frames": "0"},
        )
        assert response == {"via_url": helpers.via_url.return_value}

    @pytest.mark.usefixtures("course_copy_plugin")
    def test_via_url_copied_cant_access_page(
        self, pyramid_request, assignment_service, canvas_service, course_service
    ):
        assignment_service.get_assignment.return_value.document_url = (
            "canvas://page/course/COURSE_ID/page_id/PAGE_ID"
        )
        course_service.get_by_context_id.return_value.extra = {
            "canvas": {"custom_canvas_course_id": "OTHER_COURSE_ID"}
        }
        course_service.get_by_context_id.return_value.get_mapped_page_id.return_value = (
            "OTHER_PAGE_ID"
        )
        canvas_service.api.pages.page.side_effect = CanvasAPIError

        with pytest.raises(PageNotFoundInCourse):
            PagesAPIViews(pyramid_request).via_url()

    def test_proxy(self, canvas_service, pyramid_request, application_instance):
        pyramid_request.params["course_id"] = "COURSE_ID"
        pyramid_request.params["page_id"] = "PAGE_ID"
        canvas_service.api.pages.page.return_value = CanvasPage(
            id=1, title=sentinel.title, updated_at="updated", body=sentinel.body
        )

        response = PagesAPIViews(pyramid_request).proxy()

        canvas_service.api.pages.page.assert_called_once_with("COURSE_ID", "PAGE_ID")
        assert response == {
            "title": sentinel.title,
            "body": sentinel.body,
            "canonical_url": f"https://{application_instance.lms_host()}/courses/COURSE_ID/pages/1",
        }

    @pytest.fixture
    def pages(self):
        pages = [
            CanvasPage(id=i, title=f"title {i}", updated_at=f"updated {i}")
            for i in range(5)
        ]
        random.shuffle(pages)
        return pages

    @pytest.fixture
    def helpers(self, patch):
        return patch("lms.views.api.canvas.pages.helpers")

    @pytest.fixture
    def BearerTokenSchema(self, patch):
        return patch("lms.views.api.canvas.pages.BearerTokenSchema")
