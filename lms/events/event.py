import json
from dataclasses import dataclass, field, fields
from typing import List, Optional

from pyramid.request import Request
from sqlalchemy import inspect

from lms.db import BASE
from lms.models import EventType
from lms.services.lti_role_service import LTIRoleService


@dataclass
class BaseEvent:  # pylint:disable=too-many-instance-attributes
    """Base class for generic events."""

    Type = EventType.Type
    """Expose the type here for the callers convenience"""

    request: Request
    """Reference to the current request"""

    type: EventType.Type
    """Type of the event"""

    user_id: Optional[int] = None
    """Which user is related to this event"""

    role_ids: List[int] = field(default_factory=list)
    """Which roles does the user have in relation to this event"""

    application_instance_id: Optional[int] = None
    course_id: Optional[int] = None
    assignment_id: Optional[int] = None
    grouping_id: Optional[int] = None

    data: Optional[dict] = None
    """Extra data to associate with this event"""

    def __post_init__(self):
        for event_field in fields(self):
            getter_name = f"_get_{event_field.name}"

            # If we don't have a value for `field` and we have implemented
            # a _get_`field.name` method, use that to get a default
            if not getattr(self, event_field.name) and hasattr(self, getter_name):
                setattr(self, event_field.name, getattr(self, getter_name)())


@dataclass
class LTIEvent(BaseEvent):
    """
    Class to represent LTI-related events.

    All the _get_`field`  method are used by the base class to
    fill up any missing fields
    """

    # pylint:disable=no-member

    def _get_user_id(self):
        return self.request.user.id

    # These methods provide defaults for each field and are used in
    # `BaseEvent.__post_init__` above.
    def _get_role_ids(self):
        return [
            role.id
            for role in self.request.find_service(LTIRoleService).get_roles(
                self.request.lti_user.roles
            )
        ]

    def _get_application_instance_id(self):
        if application_instance := self.request.find_service(
            name="application_instance"
        ).get_current():
            return application_instance.id

        return None

    def _get_course_id(self):
        context_id = self.request.lti_params.get("context_id")
        if not context_id:
            try:
                # If we are deeplinking we'll get the context_id from json instead
                context_id = self.request.json.get("context_id")
            except json.decoder.JSONDecodeError:
                pass

        if course := self.request.find_service(name="course").get_by_context_id(
            context_id
        ):
            return course.id

        return None

    def _get_assignment_id(self):
        if assignment := self.request.find_service(name="assignment").get_assignment(
            self.request.lti_params.get("tool_consumer_instance_guid"),
            self.request.lti_params.get("resource_link_id"),
        ):
            return assignment.id

        return None


@dataclass
class AuditTrailEvent(BaseEvent):
    type: EventType.Type = EventType.Type.AUDIT_TRAIL

    instance: BASE = None
    """Object for which we are tracking changes"""

    action: str = None
    """What happen to the object: crated,updated,deleted..."""

    source: str = None
    """In which context the change happen"""

    def _get_data(self):
        """
        Fill the event's data value.

        This is called on BaseEvent.__post_init__
        """
        changes = {}
        instance_details = inspect(self.instance)
        for attr in instance_details.attrs:
            history = instance_details.get_history(attr.key, True)

            if not history.has_changes():
                continue

            changes[attr.key] = (
                history.deleted[0] if history.deleted else None,
                history.added[0] if history.added else None,
            )

        return {
            "model": self.instance.__class__.__name__,
            "id": self.instance.id,
            "action": self.action,
            "source": self.source,
            # LTI users will have a FK to the User table.
            # userid is useful for other authentication methods.
            # For example this will be the user's email while using google oauth.
            "userid": self.request.identity.userid,
            "changes": changes,
        }

    @staticmethod
    def notify(request: Request, instance: BASE, source="admin_pages"):
        if request.db.is_modified(instance):
            request.registry.notify(
                AuditTrailEvent(
                    request=request,
                    instance=instance,
                    action="update",
                    source=source,
                )
            )
