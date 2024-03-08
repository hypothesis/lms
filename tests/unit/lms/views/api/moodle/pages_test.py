from unittest.mock import Mock, sentinel

import pytest
from h_matchers import Any

from lms.views.api.moodle.pages import PageNotFoundInCourse, PagesAPIViews


@pytest.mark.usefixtures(
    "application_instance_service", "assignment_service", "moodle_api_client"
)
class TestPageAPIViews:
    def test_list_pages(self, moodle_api_client, pyramid_request):
        course_id = "COURSE_ID"
        pyramid_request.matchdict = {"course_id": course_id}

        result = PagesAPIViews(pyramid_request).list_pages()

        assert result == moodle_api_client.list_pages.return_value

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
        # Current course and document course are the same
        lti_user.lti.course_id = (
            course_service.get_by_context_id.return_value.lms_id
        ) = "COURSE_ID"
        assignment_service.get_assignment.return_value.document_url = (
            "moodle://page/course/COURSE_ID/page_id/PAGE_ID"
        )
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
            Any.url.with_path("/api/moodle/pages/proxy").with_query(
                {
                    "course_id": "COURSE_ID",
                    "page_id": "PAGE_ID",
                    "authorization": "TOKEN",
                }
            ),
            options={"via.proxy_frames": "0", "via.proxy_images": "0"},
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
        lti_user,
    ):
        lti_user.lti.course_id = (
            course_service.get_by_context_id.return_value.lms_id
        ) = "OTHER_COURSE_ID"
        course_service.get_by_context_id.return_value.get_mapped_page_id.return_value = (
            "OTHER_PAGE_ID"
        )
        assignment_service.get_assignment.return_value.document_url = (
            "moodle://page/course/COURSE_ID/page_id/PAGE_ID"
        )
        BearerTokenSchema.return_value.authorization_param.return_value = "TOKEN"

        response = PagesAPIViews(pyramid_request).via_url()

        helpers.via_url.assert_called_once_with(
            pyramid_request,
            Any.url.with_path("/api/moodle/pages/proxy").with_query(
                {
                    "course_id": "OTHER_COURSE_ID",
                    "page_id": "OTHER_PAGE_ID",
                    "authorization": "TOKEN",
                }
            ),
            options={"via.proxy_frames": "0", "via.proxy_images": "0"},
        )
        assert response == {"via_url": helpers.via_url.return_value}

    def test_via_url_copied_no_page_found(
        self,
        pyramid_request,
        assignment_service,
        course_service,
        course_copy_plugin,
        lti_user,
    ):
        lti_user.lti.course_id = (
            course_service.get_by_context_id.return_value.lms_id
        ) = "OTHER_COURSE_ID"
        assignment_service.get_assignment.return_value.document_url = (
            "moodle://page/course/COURSE_ID/page_id/PAGE_ID"
        )
        course_service.get_by_context_id.return_value.get_mapped_page_id.return_value = (
            "PAGE_ID"
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
        lti_user,
    ):
        lti_user.lti.course_id = (
            course_service.get_by_context_id.return_value.lms_id
        ) = "OTHER_COURSE_ID"
        assignment_service.get_assignment.return_value.document_url = (
            "moodle://page/course/COURSE_ID/page_id/PAGE_ID"
        )
        course_service.get_by_context_id.return_value.get_mapped_page_id.return_value = (
            "PAGE_ID"
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
            Any.url.with_path("/api/moodle/pages/proxy").with_query(
                {
                    "course_id": "OTHER_COURSE_ID",
                    "page_id": "OTHER_PAGE_ID",
                    "authorization": "TOKEN",
                }
            ),
            options={"via.proxy_frames": "0", "via.proxy_images": "0"},
        )
        assert response == {"via_url": helpers.via_url.return_value}

    def test_proxy(self, moodle_api_client, pyramid_request, application_instance):
        pyramid_request.params["course_id"] = "COURSE_ID"
        pyramid_request.params["page_id"] = "PAGE_ID"
        moodle_api_client.page.return_value = {
            "id": 1,
            "title": sentinel.title,
            "updated_at": "updated",
            "course_module": sentinel.course_module,
            "body": """BODY <img src="http://moodle.com/webservice/pluginfile.php/image.jpg"/>""",
        }

        response = PagesAPIViews(pyramid_request).proxy()

        moodle_api_client.page.assert_called_once_with("COURSE_ID", "PAGE_ID")
        assert response == {
            "title": sentinel.title,
            "body": """BODY <img src="http://moodle.com/pluginfile.php/image.jpg"/>""",
            "canonical_url": f"{application_instance.lms_host()}/mod/page/view.php?id=sentinel.course_module",
        }

    @pytest.fixture
    def helpers(self, patch):
        return patch("lms.views.api.moodle.pages.helpers")

    @pytest.fixture
    def BearerTokenSchema(self, patch):
        return patch("lms.views.api.moodle.pages.BearerTokenSchema")
