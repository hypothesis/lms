import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from sqlalchemy import distinct, func, or_, select, tuple_
from sqlalchemy.dialects.postgresql import aggregate_order_by
from sqlalchemy.orm import aliased

from lms.models import (
    Assignment,
    AssignmentGrouping,
    AssignmentMembership,
    Course,
    Grouping,
    LTIRole,
    User,
)
from lms.services.email_preferences import EmailPreferencesService
from lms.services.h_api import HAPI
from lms.services.mailchimp import EmailRecipient, EmailSender
from lms.tasks.mailchimp import send

LOG = logging.getLogger(__name__)


class DigestService:
    """A service for generating "digests" (activity reports)."""

    def __init__(
        self, db, h_api, sender, email_preferences_service: EmailPreferencesService
    ):
        self._db = db
        self._h_api = h_api
        self._email_preferences_service = email_preferences_service
        self._sender = sender

    def send_instructor_email_digest(  # noqa: PLR0913
        self,
        h_userid,
        created_after,
        created_before,
        override_to_email=None,
        deduplicate=True,
    ):
        """Send instructor email digests for the given users and timeframe."""
        annotation_dicts = self._h_api.get_annotations(
            h_userid, created_after, created_before
        )

        annotations = [
            Annotation.make(annotation_dict) for annotation_dict in annotation_dicts
        ]

        context = DigestContext(self._db, h_userid, annotations)

        digest = context.instructor_digest(context.user_info.h_userid)

        if not digest["total_annotations"]:
            # This user has no activity.
            return

        digest["preferences_url"] = self._email_preferences_service.preferences_url(
            context.user_info.h_userid, "instructor_digest"
        )

        if override_to_email is None:
            to_email = context.user_info.email
        else:
            to_email = override_to_email

        if not to_email:
            # We don't have an email address for this user.
            return

        if deduplicate:
            task_done_key = f"instructor_email_digest::{context.user_info.h_userid}::{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
            task_done_data = {
                "type": "instructor_email_digest",
                "h_userid": context.user_info.h_userid,
                "created_before": created_before.isoformat(),
            }
        else:
            task_done_key = None
            task_done_data = None

        send.delay(
            task_done_key=task_done_key,
            task_done_data=task_done_data,
            template="lms:templates/email/instructor_email_digest/",
            sender=asdict(self._sender),
            recipient=asdict(EmailRecipient(to_email, context.user_info.display_name)),
            template_vars=digest,
            unsubscribe_url=self._email_preferences_service.unsubscribe_url(
                context.user_info.h_userid, "instructor_digest"
            ),
        )


@dataclass(frozen=True, order=True)
class AssignmentInfo:
    """Information about an assignment."""

    id: int
    """The assignment's ID (Assignment.id)."""

    guid: str
    """The tool_consumer_instance_guid of the assignment's LMS (Assignment.tool_consumer_instance_guid)."""

    resource_link_id: str
    """The assignment's resource_link_id (Assignment.resource_link_id)."""

    title: str
    """The assignment's title (Assignment.title)."""

    authority_provided_id: str
    """The authority_provided_id of the assignment's course (Course.authority_provided_id)."""


@dataclass(frozen=True)
class Annotation:
    """Info about an annotation from the h API."""

    userid: str
    """The annotation's h userid."""

    authority_provided_id: str
    """The authority_provided_id of the annotation's group.

    This may be the ID of a non-course grouping that the annotation belongs to
    such as a Canvas section or a Canvas group, or it may be the ID of the
    annotation's course group.
    """

    guid: str
    """The tool_consumer_instance_guid of the annotation's LMS."""

    resource_link_id: str
    """The resource_link_id of the annotation's assignment."""

    @classmethod
    def make(cls, annotation_dict):
        """Make an Annotation from an annotation dict from the h bulk annotation API."""
        userid = annotation_dict["author"]["userid"]
        authority_provided_id = annotation_dict["group"]["authority_provided_id"]
        metadata = annotation_dict["metadata"]

        try:
            guid = metadata["lms"]["guid"]
        except (KeyError, TypeError):
            guid = None

        try:
            resource_link_id = metadata["lms"]["assignment"]["resource_link_id"]
        except (KeyError, TypeError):
            resource_link_id = None

        return cls(
            userid=userid,
            authority_provided_id=authority_provided_id,
            guid=guid,
            resource_link_id=resource_link_id,
        )


@dataclass(frozen=True)
class UserInfo:
    """All User's for a given h_userid, unified across all ApplicationInstance's."""

    h_userid: str
    email: str | None
    display_name: str | None


@dataclass(frozen=True)
class CourseInfo:
    """All Course's for a given authority_provided_id, unified across all ApplicationInstance's."""

    authority_provided_id: str
    title: str | None
    instructor_h_userids: tuple[str]
    learner_annotations: tuple[dict]


class DigestContext:
    """A context/helper object for DigestService."""

    def __init__(self, db, h_userid, annotations):
        self._db = db
        self.h_userid = h_userid
        self.annotations = annotations
        self._assignment_infos = None
        self._user_info = None
        self._course_infos = None

    def instructor_digest(self, h_userid):
        """
        Return a digest (dict of template variables) for the given instructor.

        The digest will only include courses in which both:

        1. The user is an instructor
        2. There are annotations by learners
        """
        course_digests = []

        for course_info in self.course_infos:
            num_annotations = len(course_info.learner_annotations)

            if not num_annotations:
                # There was no activity in this course.
                continue

            if h_userid not in course_info.instructor_h_userids:
                # The user isn't an instructor in this course.
                continue

            course_assignments = []

            for assignment_info in self.assignment_infos:
                if (
                    assignment_info.authority_provided_id
                    != course_info.authority_provided_id
                ):
                    continue

                assignment_learner_annotations = [
                    annotation
                    for annotation in course_info.learner_annotations
                    if annotation.guid == assignment_info.guid
                    and annotation.resource_link_id == assignment_info.resource_link_id
                ]

                course_assignments.append(
                    {
                        "title": assignment_info.title,
                        "num_annotations": len(assignment_learner_annotations),
                        "annotators": list(
                            set(
                                annotation.userid
                                for annotation in assignment_learner_annotations
                            )
                        ),
                    }
                )

            course_digests.append(
                {
                    "title": course_info.title,
                    "num_annotations": num_annotations,
                    "annotators": list(
                        set(
                            annotation.userid
                            for annotation in course_info.learner_annotations
                        )
                    ),
                    "assignments": course_assignments,
                }
            )

        return {
            "total_annotations": sum(
                course_digest["num_annotations"] for course_digest in course_digests
            ),
            "annotators": list(
                set(
                    annotator
                    for course_digest in course_digests
                    for annotator in course_digest["annotators"]
                )
            ),
            "courses": course_digests,
        }

    @property
    def assignment_infos(self):
        """Return the list of AssignmentInfo's for all the assignment IDs in self.annotations."""
        if self._assignment_infos is None:
            self._assignment_infos = [
                AssignmentInfo(
                    row.id,
                    row.tool_consumer_instance_guid,
                    row.resource_link_id,
                    row.title,
                    row.authority_provided_id,
                )
                for row in self._db.execute(
                    select(
                        Assignment.id,
                        Assignment.tool_consumer_instance_guid,
                        Assignment.resource_link_id,
                        Assignment.title,
                        Course.authority_provided_id,
                    ).where(
                        tuple_(
                            Assignment.tool_consumer_instance_guid,
                            Assignment.resource_link_id,
                        ).in_(
                            [
                                (annotation.guid, annotation.resource_link_id)
                                for annotation in self.annotations
                                if annotation.guid is not None
                                and annotation.resource_link_id is not None
                            ]
                        ),
                        AssignmentGrouping.assignment_id == Assignment.id,
                        AssignmentGrouping.grouping_id == Course.id,
                        Assignment.title.is_not(None),
                    )
                ).all()
                if row.title.strip()
            ]

        return self._assignment_infos

    @property
    def user_info(self):
        """Return a UserInfo for self.h_userid."""
        if self._user_info is not None:
            return self._user_info

        row = self._db.execute(
            select(
                # pylint:disable=not-callable
                User.h_userid,
                # The most recent email address for each h_userid.
                func.array_agg(aggregate_order_by(User.email, User.updated.desc()))
                .filter(User.email.isnot(None))[1]
                .label("email"),
                # The most recent display_name address for each h_userid.
                func.array_agg(
                    aggregate_order_by(User.display_name, User.updated.desc())
                )
                .filter(User.display_name.isnot(None))[1]
                .label("display_name"),
            )
            .where(User.h_userid == self.h_userid)
            .group_by(User.h_userid)
        ).one()

        self._user_info = UserInfo(row.h_userid, row.email, row.display_name)

        return self._user_info

    @property
    def course_infos(self):
        """Return a list of CourseInfo's for all the courses in self.annotations."""
        if self._course_infos is not None:
            return self._course_infos

        authority_provided_ids = set(
            annotation.authority_provided_id for annotation in self.annotations
        )

        # We're going to be joining the grouping table to itself and this requires
        # us to create an alias for one side of the join, see:
        # https://docs.sqlalchemy.org/en/20/orm/self_referential.html#self-referential-query-strategies
        grouping_aliased = aliased(Grouping)

        query = (
            select(
                # pylint:disable=not-callable
                Course.authority_provided_id,
                # All authority_provided_id's associated with each authority_provided_id.
                # This includes the authority_provided_id of the course group
                # and the authority_provided_id's of any sub-groupings.
                func.array_agg(distinct(grouping_aliased.authority_provided_id))
                .filter(grouping_aliased.id.is_not(None))
                .label("authority_provided_ids"),
                # The most recent name for each course.
                func.array_agg(
                    aggregate_order_by(Course.lms_name, Course.updated.desc())
                )
                .filter(Course.lms_name.isnot(None))[1]
                .label("lms_name"),
                # The h_userids of all known instructors in each course.
                func.array_agg(distinct(User.h_userid))
                .filter(LTIRole.type == "instructor", LTIRole.scope == "course")
                .label("instructor_h_userids"),
            )
            # Join to models.Grouping in order to find both course- and
            # sub-groupings for each authority_provided_id.
            .join(
                grouping_aliased,
                or_(
                    grouping_aliased.id == Course.id,
                    grouping_aliased.parent_id == Course.id,
                ),
            )
            .where(grouping_aliased.authority_provided_id.in_(authority_provided_ids))
            # Join to a few tables to find the instructors for each course.
            .outerjoin(AssignmentGrouping, AssignmentGrouping.grouping_id == Course.id)
            .outerjoin(
                AssignmentMembership,
                AssignmentMembership.assignment_id == AssignmentGrouping.assignment_id,
            )
            .outerjoin(LTIRole, LTIRole.id == AssignmentMembership.lti_role_id)
            .outerjoin(User, User.id == AssignmentMembership.user_id)
            .group_by(Course.authority_provided_id)
        )

        self._course_infos = []

        for row in self._db.execute(query):
            # SQLAlchemy returns None instead of [].
            authority_provided_ids = row.authority_provided_ids or []
            instructor_h_userids = row.instructor_h_userids or []

            self._course_infos.append(
                CourseInfo(
                    authority_provided_id=row.authority_provided_id,
                    title=row.lms_name,
                    instructor_h_userids=tuple(instructor_h_userids),
                    learner_annotations=tuple(
                        annotation
                        for annotation in self.annotations
                        if annotation.authority_provided_id in authority_provided_ids
                        and annotation.userid not in instructor_h_userids
                    ),
                )
            )

        return self._course_infos


def service_factory(_context, request):
    return DigestService(
        db=request.db,
        h_api=request.find_service(HAPI),
        email_preferences_service=request.find_service(EmailPreferencesService),
        sender=EmailSender(
            request.registry.settings.get("mailchimp_digests_subaccount"),
            request.registry.settings.get("mailchimp_digests_email"),
            request.registry.settings.get("mailchimp_digests_name"),
        ),
    )
