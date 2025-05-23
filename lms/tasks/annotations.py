import logging

from pydantic import BaseModel
from sqlalchemy import select

from lms.models import Assignment, LMSUser
from lms.services.annotation_activity_email import AnnotationActivityEmailService
from lms.tasks.celery import app


class _AssignmentMetadata(BaseModel):
    resource_link_id: str


class _LMSMetadata(BaseModel):
    guid: str
    assignment: _AssignmentMetadata


class _AnnotationMetadata(BaseModel):
    lms: _LMSMetadata


class _AnnotationMention(BaseModel):
    userid: str


class _AnnotationPermissions(BaseModel):
    read: list[str]
    admin: list[str]
    update: list[str]
    delete: list[str]

    @property
    def is_private(self) -> bool:
        # Private annotations have the same read permissions as the rest, the userid.
        return self.read[0] == self.admin[0] == self.update[0] == self.delete[0]


class _Annotation(BaseModel):
    id: str
    user: str
    permissions: _AnnotationPermissions
    mentions: list[_AnnotationMention]
    metadata: _AnnotationMetadata
    text_rendered: str
    quote: str | None


class AnnotationEvent(BaseModel):
    action: str
    annotation: _Annotation


LOG = logging.getLogger(__name__)


@app.task
def annotation_event(*, event) -> None:
    """
    Process annotations events.

    These are published directly on LMS's queue by H
    """
    annotation_event = AnnotationEvent(**event)
    annotation = annotation_event.annotation

    if annotation_event.action not in {"create", "update"}:
        LOG.info("Skipping event type %s", annotation_event.action)
        return

    if annotation.permissions.is_private:
        LOG.info("Skipping private annotation %s", annotation.id)
        return

    guid = annotation.metadata.lms.guid
    resource_link_id = annotation.metadata.lms.assignment.resource_link_id

    with app.request_context() as request, request.tm:
        db = request.db
        annotation_activity_email_service = request.find_service(
            AnnotationActivityEmailService
        )

        mentioning_user = db.execute(
            select(LMSUser).where(LMSUser.h_userid == annotation.user)
        ).scalar_one()
        assignment = db.execute(
            select(Assignment).where(
                Assignment.tool_consumer_instance_guid == guid,
                Assignment.resource_link_id == resource_link_id,
            )
        ).scalar_one()

        for mention in annotation.mentions:
            mentioned_user = db.execute(
                select(LMSUser).where(LMSUser.h_userid == mention.userid)
            ).scalar_one()

            if not mentioned_user.email:
                LOG.info(
                    "Mentioned user %s has no email address", mentioned_user.h_userid
                )
                continue

            if mentioned_user == mentioning_user:
                LOG.info("Skipping self-mention of user %s", mentioned_user.h_userid)
                continue

            LOG.info(
                "Processing mention from '%s' to '%s' in assignment '%s'",
                mentioning_user.h_userid,
                mentioned_user.h_userid,
                assignment.title,
            )
            annotation_activity_email_service.send_mention(
                annotation.id,
                annotation.text_rendered,
                annotation.quote,
                mentioning_user.h_userid,
                mentioned_user.h_userid,
                assignment.id,
            )
