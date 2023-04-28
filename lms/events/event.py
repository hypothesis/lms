import json
from dataclasses import asdict, dataclass, field, fields
from typing import Dict, List, Optional

from pyramid.request import Request
from sqlalchemy import inspect

from lms.db import BASE
from lms.models import EventType


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
        return [role.id for role in self.request.lti_user.lti_roles]

    def _get_application_instance_id(self):
        return self.request.lti_user.application_instance_id

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
    @dataclass
    class ModelChange:
        action: str
        model: str
        id: int  # pylint: disable=invalid-name
        source: str
        userid: str
        changes: Dict[str, tuple]

        @classmethod
        def from_instance(cls, instance, **kwargs):
            changes = {}
            instance_details = inspect(instance)
            for attr in instance_details.attrs:
                history = instance_details.get_history(attr.key, True)

                if not history.has_changes():
                    continue

                changes[attr.key] = (
                    history.deleted[0] if history.deleted else None,
                    history.added[0] if history.added else None,
                )

            return cls(
                model=instance.__class__.__name__,
                id=instance.id,
                changes=changes,
                **kwargs,
            )

    type: EventType.Type = EventType.Type.AUDIT_TRAIL
    change: ModelChange = None

    def _get_data(self):
        """
        Fill the event's data value.

        This is called on BaseEvent.__post_init__
        """
        return asdict(self.change)

    @staticmethod
    def notify(request: Request, instance: BASE, source="admin_pages"):
        if request.db.is_modified(instance):
            request.registry.notify(
                AuditTrailEvent(
                    request=request,
                    change=AuditTrailEvent.ModelChange.from_instance(
                        instance,
                        action="update",
                        source=source,
                        # LTI users will have a FK to the User table.
                        # userid is useful for other authentication methods.
                        # For example this will be the user's email while using google oauth.
                        userid=request.identity.userid,
                    ),
                )
            )
