from dataclasses import asdict, dataclass, field, fields

from pyramid.request import Request
from sqlalchemy import inspect

from lms.db import Base
from lms.models import EventType


@dataclass
class BaseEvent:
    """Base class for generic events."""

    type: EventType.Type
    """Type of the event"""

    request: Request
    """Reference to the current request"""

    user_id: int | None = None
    """Which user is related to this event"""

    role_ids: list[int] = field(default_factory=list)
    """Which roles does the user have in relation to this event"""

    application_instance_id: int | None = None
    course_id: int | None = None
    assignment_id: int | None = None
    grouping_id: int | None = None

    data: dict | None = None
    """Extra data to associate with this event"""

    Type = EventType.Type
    """Expose the type here for the callers convenience"""

    def serialize(self) -> dict:
        return {
            field.name: getattr(self, field.name)
            for field in fields(self)
            # Excluded non-serializable fields
            if field.name not in ["request", "Type"]
        }


@dataclass
class LTIEvent(BaseEvent):
    """Class to represent LTI-related events."""

    @classmethod
    def from_request(
        cls, request: Request, type_: EventType.Type, data: dict | None = None
    ):
        if not request.lti_user:
            return cls(request=request, type=type_, data=data)

        course_id = None
        assignment_id = None
        if course := request.find_service(name="course").get_by_context_id(
            request.lti_user.lti.course_id
        ):
            course_id = course.id

        if assignment := request.find_service(name="assignment").get_assignment(
            request.lti_user.tool_consumer_instance_guid,
            request.lti_user.lti.assignment_id,
        ):
            assignment_id = assignment.id

        return cls(
            request=request,
            type=type_,
            user_id=request.user.id,
            role_ids=[role.id for role in request.lti_user.lti_roles],
            application_instance_id=request.lti_user.application_instance_id,
            course_id=course_id,
            assignment_id=assignment_id,
            data=data,
        )


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


@dataclass
class AuditTrailEvent(BaseEvent):
    @staticmethod
    def notify(request: Request, instance: Base, source="admin_pages"):
        db = request.db
        model_changes = None
        if db.is_modified(instance):
            model_changes = ModelChange.from_instance(
                instance,
                action="insert" if instance in db.new else "update",
                source=source,
                userid=request.identity.userid,
            )
        elif instance in db.deleted:
            model_changes = ModelChange(
                model=instance.__class__.__name__,
                id=instance.id,
                action="delete",
                source=source,
                userid=request.identity.userid,
                changes={},
            )

        if model_changes:
            request.registry.notify(
                AuditTrailEvent(
                    type=EventType.Type.AUDIT_TRAIL,
                    request=request,
                    data=asdict(model_changes),
                )
            )


def _serialize_change(value):
    """Serialize in a DB compatible manner a DB change."""
    if isinstance(value, Base):
        if hasattr(value, "id"):
            # If we have a model with simple PK, use that, it would make
            # our lives easier in case we have to write SQL consulting these values
            return value.id
        # Just convert it to a string otherwise
        return str(value)

    return value
