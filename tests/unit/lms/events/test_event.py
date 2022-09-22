import json
from unittest.mock import Mock, sentinel

import pytest

from lms.events import AuditTrailEvent, LTIEvent
from tests import factories


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

        course_service.get_by_context_id.assert_called_once_with(sentinel.context_id)
        assert event.course_id == course_service.get_by_context_id.return_value.id

        assignment_service.get_assignment.assert_called_once_with(
            sentinel.tool_guid, sentinel.resource_link_id
        )
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
    def test_lti_event_when_context_id_from_json(self, pyramid_request, course_service):
        del pyramid_request.lti_params["context_id"]
        pyramid_request.json = {"context_id": sentinel.json_context_id}

        event = LTIEvent(request=pyramid_request, type=sentinel.type)

        course_service.get_by_context_id.assert_called_once_with(
            sentinel.json_context_id
        )
        assert event.course_id == course_service.get_by_context_id.return_value.id

    @pytest.mark.usefixtures(
        "lti_role_service", "application_instance_service", "assignment_service"
    )
    def test_lti_event_when_context_id_from_invalid_json(
        self, pyramid_request, course_service
    ):
        del pyramid_request.lti_params["context_id"]

        event = LTIEvent(request=pyramid_request, type=sentinel.type)

        course_service.get_by_context_id.assert_called_once_with(None)
        assert event.course_id == course_service.get_by_context_id.return_value.id

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

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.json = Mock()
        pyramid_request.json.get.side_effect = json.decoder.JSONDecodeError(
            msg="", doc="", pos=0
        )

        pyramid_request.lti_params.update(
            {
                "context_id": sentinel.context_id,
                "tool_consumer_instance_guid": sentinel.tool_guid,
                "resource_link_id": sentinel.resource_link_id,
            }
        )

        return pyramid_request


class TestAuditTrailEvent:
    def test_model_change_from_instance(self, db_session):
        org = factories.Organization(name="OLD_NAME", enabled=True)
        db_session.flush()
        org.name = "NEW_NAME"
        org.enabled = False

        assert AuditTrailEvent.ModelChange.from_instance(
            org, action=sentinel.action, source=sentinel.source, userid=sentinel.userid
        ) == AuditTrailEvent.ModelChange(
            model="Organization",
            id=org.id,
            source=sentinel.source,
            action=sentinel.action,
            userid=sentinel.userid,
            changes={"name": ("OLD_NAME", "NEW_NAME"), "enabled": (True, False)},
        )

    def test__get_data(self, pyramid_request):
        kwargs = {
            "id": sentinel.id,
            "model": sentinel.model,
            "source": sentinel.source,
            "action": sentinel.action,
            "userid": sentinel.userid,
            "changes": sentinel.changes,
        }

        event = AuditTrailEvent(
            request=pyramid_request, change=AuditTrailEvent.ModelChange(**kwargs)
        )

        assert event.data == kwargs

    def test_notify_update_with_changes(self, pyramid_request, db_session):
        org = factories.Organization(name="OLD_NAME", enabled=True)
        db_session.flush()
        org.name = "NEW_NAME"

        AuditTrailEvent.notify(pyramid_request, org, source=sentinel.source)

        pyramid_request.registry.notify.assert_called_once_with(
            AuditTrailEvent(
                request=pyramid_request,
                change=AuditTrailEvent.ModelChange(
                    id=org.id,
                    model="Organization",
                    action="update",
                    source=sentinel.source,
                    userid=pyramid_request.identity.userid,
                    changes={"name": ("OLD_NAME", "NEW_NAME")},
                ),
            )
        )

    def test_notify_no_changes(self, pyramid_request, db_session):
        org = factories.Organization(name="OLD_NAME", enabled=True)
        db_session.flush()

        AuditTrailEvent.notify(pyramid_request, org, source=sentinel.source)

        pyramid_request.registry.notify.assert_not_called()
