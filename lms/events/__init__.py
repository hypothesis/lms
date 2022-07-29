from dataclasses import dataclass, field
from typing import List, Optional

from pyramid.events import subscriber
from pyramid.request import Request

from lms.models import EventType
from lms.services import EventService, LTIRoleService


@dataclass
class BaseEvent:  # pylint:disable=too-many-instance-attributes
    request: Request
    type: EventType.Type

    user_id: Optional[int] = None
    role_ids: List[int] = field(default_factory=list)
    application_instance_id: Optional[int] = None
    course_id: Optional[int] = None
    assignment_id: Optional[int] = None
    grouping_id: Optional[int] = None
    data: Optional[dict] = None


@dataclass
class LTIEvent(BaseEvent):
    def __post_init__(self):
        # pylint:disable=no-member
        if not self.user_id:
            self.user_id = self.request.user.id

        if not self.role_ids:
            self.role_ids = [
                role.id
                for role in self.request.find_service(LTIRoleService).get_roles(
                    self.request.lti_params.get("roles")
                )
            ]

        if not self.application_instance_id:
            if application_instance := self.request.find_service(
                name="application_instance"
            ).get_current():
                self.application_instance_id = application_instance.id

        if not self.course_id:
            if course := self.request.find_service(name="course").get_by_context_id(
                self.request.lti_params.get("context_id")
            ):
                self.course_id = course.id

        if not self.assignment_id:
            self.assignment_id = (
                self.request.find_service(name="assignment")
                .get_assignment(
                    self.request.lti_params.get("tool_consumer_instance_guid"),
                    self.request.lti_params.get("resource_link_id"),
                )
                .id
            )


@subscriber(BaseEvent)
def handle_event(event: BaseEvent):
    # Record the event in the Event model's table
    event.request.find_service(EventService).insert_event(event)


def includeme(_config):  # pragma: no cover
    pass
