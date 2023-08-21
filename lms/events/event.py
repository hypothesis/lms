from dataclasses import asdict, dataclass, field, fields
from typing import Optional

from pyramid.request import Request
from sqlalchemy import inspect

from lms.db import BASE
from lms.models import EventType


@dataclass
class BaseEvent:  # pylint:disable=too-many-instance-attributes
    """Base class for generic events."""

    Type = EventType.Type
    """Expose the type here for the callers convenience"""

    type: EventType.Type
    """Type of the event"""

    request: Optional[Request] = None
    """Reference to the current request"""

    user_id: Optional[int] = None
    """Which user is related to this event"""

    role_ids: list[int] = field(default_factory=list)
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

    def serialize(self) -> dict:
        return {
            field.name: getattr(self, field.name)
            for field in fields(self)
            # Excluded non-serializable fields
            if field.name not in ["request"]
        }


@dataclass
class LTIEvent(BaseEvent):
    """
    Class to represent LTI-related events.

    All the _get_`field`  method are used by the base class to
    fill up any missing fields
    """

    def _get_user_id(self):
        return self.request.user.id

    # These methods provide defaults for each field and are used in
    # `BaseEvent.__post_init__` above.
    def _get_role_ids(self):
        return [role.id for role in self.request.lti_user.lti_roles]

    def _get_application_instance_id(self):
        return self.request.lti_user.application_instance_id

    def _get_course_id(self):
        if course := self.request.find_service(name="course").get_by_context_id(
            self.request.lti_user.lti.course_id
        ):
            return course.id

        return None

    def _get_assignment_id(self):
        if assignment := self.request.find_service(name="assignment").get_assignment(
            self.request.lti_user.tool_consumer_instance_guid,
            self.request.lti_user.lti.assignment_id,
        ):
            return assignment.id

        return None


@dataclass
class AuditTrailEvent(BaseEvent):
    @dataclass
    class ModelChange:
        action: str
        model: str
        id: int
        source: str
        # LTI users will have a FK to the User table.
        # userid is useful for other authentication methods.
        # For example this will be the user's email while using google oauth.
        userid: str
        changes: dict[str, tuple]

        @classmethod
        def from_instance(cls, instance, **kwargs):
            changes = {}
            instance_details = inspect(instance)
            for attr in instance_details.attrs:
                history = instance_details.get_history(attr.key, True)

                if not history.has_changes():
                    continue

                changes[attr.key] = (
                    _serialize_change(history.deleted[0]) if history.deleted else None,
                    _serialize_change(history.added[0]) if history.added else None,
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
        db = request.db
        if db.is_modified(instance):
            request.registry.notify(
                AuditTrailEvent(
                    request=request,
                    change=AuditTrailEvent.ModelChange.from_instance(
                        instance,
                        action="insert" if instance in db.new else "update",
                        source=source,
                        userid=request.identity.userid,
                    ),
                )
            )
        elif instance in db.deleted:
            request.registry.notify(
                AuditTrailEvent(
                    request=request,
                    change=AuditTrailEvent.ModelChange(
                        model=instance.__class__.__name__,
                        id=instance.id,
                        action="delete",
                        source=source,
                        userid=request.identity.userid,
                        changes={},
                    ),
                )
            )


def _serialize_change(value):
    """Serialize in a DB compatible manner a DB change."""
    if isinstance(value, BASE):
        if hasattr(value, "id"):
            # If we have a model with simple PK, use that, it would make
            # our lives easier in case we have to write SQL consulting these values
            return value.id
        # Just convert it to a string otherwise
        return str(value)

    return value
