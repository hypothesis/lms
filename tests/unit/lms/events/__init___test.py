from unittest.mock import sentinel

import pytest

from lms.events import BaseEvent, LTIEvent, handle_event


def test_handle_event(event_service, pyramid_request):
    event = BaseEvent(request=pyramid_request, type=sentinel.type)

    handle_event(event)

    event_service.insert_event.assert_called_once_with(event)


class TestLTIEvent:
    def test_lti_event(
        self,
        pyramid_request,
        lti_role_service,
        application_instance_service,
        course_service,
        assignment_service,
    ):

        lti_role_service.get_roles.return_value = [sentinel]
        event = LTIEvent(request=pyramid_request, type=sentinel.type)

        assert event.user_id == pyramid_request.user.id
        assert event.role_ids == [sentinel.id]
        assert (
            event.application_instance_id
            == application_instance_service.get_current.return_value.id
        )
        assert event.course_id == course_service.get_by_context_id.return_value.id
        assert event.assignment_id == assignment_service.get_assignment.return_value.id

    @pytest.mark.usefixtures("lti_role_service", "course_service", "assignment_service")
    def test_lti_event_when_no_application_instance(
        self, pyramid_request, application_instance_service
    ):
        application_instance_service.get_current.return_value = None

        event = LTIEvent(request=pyramid_request, type=sentinel.type)
        assert not event.application_instance_id

    @pytest.mark.usefixtures(
        "lti_role_service", "application_instance_service", "assignment_service"
    )
    def test_lti_event_when_no_course(self, pyramid_request, course_service):
        course_service.get_by_context_id.return_value = None

        event = LTIEvent(request=pyramid_request, type=sentinel.type)
        assert not event.course_id

    @pytest.mark.usefixtures(
        "lti_role_service", "application_instance_service", "course_service"
    )
    def test_lti_event_when_no_assignment(self, pyramid_request, assignment_service):
        assignment_service.get_assignment.return_value = None

        event = LTIEvent(request=pyramid_request, type=sentinel.type)
        assert not event.assignment_id

    def test_lti_event_with_values(self, pyramid_request):
        event = LTIEvent(
            request=pyramid_request,
            type=sentinel.type,
            user_id=sentinel.user_id,
            role_ids=sentinel.role_ids,
            application_instance_id=sentinel.application_instance_id,
            course_id=sentinel.course_id,
            assignment_id=sentinel.assignment_id,
        )

        assert event.user_id == sentinel.user_id
        assert event.role_ids == sentinel.role_ids
        assert event.application_instance_id == sentinel.application_instance_id
        assert event.course_id == sentinel.course_id
        assert event.assignment_id == sentinel.assignment_id
