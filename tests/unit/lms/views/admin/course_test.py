from unittest.mock import Mock, sentinel

import pytest
from h_matchers import Any
from pyramid.httpexceptions import HTTPFound, HTTPNotFound

from lms.models import EventType
from lms.services import InvalidPublicId
from lms.views.admin.course import AdminCourseViews
from tests import factories


@pytest.mark.usefixtures("course_service", "organization_service")
class TestAdminCourseViews:
    def test_show(self, pyramid_request, course_service, views):
        pyramid_request.matchdict["id_"] = sentinel.id_

        response = views.show()

        course_service.get_by_id.assert_called_once_with(id_=sentinel.id_)

        assert response == {
            "course": course_service.get_by_id.return_value,
        }

    def test_show_not_found(self, pyramid_request, course_service, views):
        pyramid_request.matchdict["id_"] = sentinel.id_
        course_service.get_by_id.return_value = None

        with pytest.raises(HTTPNotFound):
            views.show()

    def test_course_dashboard(
        self,
        pyramid_request,
        course_service,
        views,
        AuditTrailEvent,
        course,
        organization,
    ):
        pyramid_request.matchdict["id_"] = sentinel.id
        course_service.get_by_id.return_value = course

        response = views.course_dashboard()

        AuditTrailEvent.assert_called_once_with(
            request=pyramid_request,
            type=EventType.Type.AUDIT_TRAIL,
            data={
                "action": "view_dashboard",
                "id": course.id,
                "model": "Course",
                "source": "admin_pages",
                "userid": "TEST_USER_ID",
                "changes": {},
            },
        )
        pyramid_request.registry.notify.has_call_with(AuditTrailEvent.return_value)
        assert response == Any.instance_of(HTTPFound).with_attrs(
            {
                "location": f"http://example.com/dashboard/orgs/{organization.public_id}/courses/{course.id}",
            }
        )

    def test_search(self, pyramid_request, course_service, views):
        pyramid_request.params["context_id"] = " PUBLIC_ID "
        pyramid_request.params["name"] = " NAME "
        pyramid_request.params["id"] = " 100 "
        pyramid_request.params["h_id"] = " H_ID "

        result = views.search()

        course_service.search.assert_called_once_with(
            id_="100",
            name="NAME",
            context_id="PUBLIC_ID",
            h_id="H_ID",
            organization_ids=[],
        )
        assert result == {"courses": course_service.search.return_value}

    def test_search_by_public_id(
        self, pyramid_request, views, organization_service, course_service
    ):
        pyramid_request.params["org_public_id"] = " PUBLIC_ID "
        organization_service.get_by_public_id.return_value = Mock(id=sentinel.id)

        views.search()

        organization_service.get_hierarchy_ids.assert_called_once_with(
            sentinel.id, include_parents=False
        )
        course_service.search.assert_called_once_with(
            id_="",
            name="",
            context_id="DUMMY-CONTEXT-ID",
            h_id="",
            organization_ids=organization_service.get_hierarchy_ids.return_value,
        )

    def test_search_invalid_public_id(
        self, pyramid_request, views, organization_service
    ):
        pyramid_request.params["org_public_id"] = " PUBLIC_ID "
        organization_service.get_by_public_id.side_effect = InvalidPublicId

        views.search()

        assert pyramid_request.session.peek_flash("errors")

    def test_search_invalid(self, pyramid_request, views):
        pyramid_request.params["id"] = "not a number"

        assert not views.search()
        assert pyramid_request.session.peek_flash

    def test_blank_search(self, views, course_service):
        views.search()

        course_service.search.assert_called_once_with(
            id_="", name="", context_id="DUMMY-CONTEXT-ID", h_id="", organization_ids=[]
        )

    @pytest.fixture
    def course(self, application_instance, db_session):
        course = factories.Course(application_instance=application_instance)
        db_session.flush()  # Give the DB objects IDs
        return course

    @pytest.fixture
    def AuditTrailEvent(self, patch):
        return patch("lms.views.admin.course.AuditTrailEvent")

    @pytest.fixture
    def views(self, pyramid_request):
        return AdminCourseViews(pyramid_request)
