from unittest.mock import sentinel

import pytest
from h_matchers import Any
from pyramid.httpexceptions import HTTPFound, HTTPNotFound

from lms.models import EventType
from lms.views.admin.assignment import AdminAssignmentViews
from tests import factories


class TestAdminAssignmentViews:
    def test_show(self, pyramid_request, assignment_service, views):
        pyramid_request.matchdict["id_"] = sentinel.id

        response = views.show()

        assignment_service.get_by_id.assert_called_once_with(id_=sentinel.id)

        assert response == {
            "assignment": assignment_service.get_by_id.return_value,
        }

    def test_show_not_found(self, pyramid_request, assignment_service, views):
        pyramid_request.matchdict["id_"] = sentinel.id
        assignment_service.get_by_id.return_value = None

        with pytest.raises(HTTPNotFound):
            views.show()

    def test_assignment_dashboard(
        self,
        pyramid_request,
        assignment_service,
        views,
        AuditTrailEvent,
        assignment,
        organization,
    ):
        pyramid_request.matchdict["id_"] = sentinel.id
        assignment_service.get_by_id.return_value = assignment

        response = views.assignment_dashboard()

        AuditTrailEvent.assert_called_once_with(
            request=pyramid_request,
            type=EventType.Type.AUDIT_TRAIL,
            data={
                "action": "view_dashboard",
                "model": "Assignment",
                "id": assignment.id,
                "source": "admin_pages",
                "userid": "TEST_USER_ID",
                "changes": {},
            },
        )
        pyramid_request.registry.notify.has_call_with(AuditTrailEvent.return_value)
        assert response == Any.instance_of(HTTPFound).with_attrs(
            {
                "location": f"http://example.com/dashboard/organization/{organization._public_id}/assignment/{assignment.id}",  # noqa: SLF001
            }
        )

    @pytest.fixture
    def assignment(self, application_instance, db_session):
        assignment = factories.Assignment()
        course = factories.Course(application_instance=application_instance)
        factories.AssignmentGrouping(assignment=assignment, grouping=course)
        db_session.flush()  # Give the DB objects IDs
        return assignment

    @pytest.fixture
    def AuditTrailEvent(self, patch):
        return patch("lms.views.admin.assignment.AuditTrailEvent")

    @pytest.fixture
    def views(self, pyramid_request):
        return AdminAssignmentViews(pyramid_request)
