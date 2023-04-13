import logging
from dataclasses import dataclass
from typing import Optional, Tuple

from h_pyramid_sentry import report_exception
from sqlalchemy import distinct, func, or_, select
from sqlalchemy.dialects.postgresql import aggregate_order_by
from sqlalchemy.orm import aliased

from lms.models import (
    AssignmentGrouping,
    AssignmentMembership,
    Course,
    EmailUnsubscribe,
    Grouping,
    LTIRole,
    User,
)
from lms.services.email_unsubscribe import EmailUnsubscribeService
from lms.services.h_api import HAPI
from lms.services.mailchimp import (
    EmailRecipient,
    EmailSender,
    MailchimpError,
    MailchimpService,
)

LOG = logging.getLogger(__name__)


class SendDigestsError(Exception):
    """An error when sending a batch of email digests."""

    def __init__(self, errors):
        super().__init__(errors)
        self.errors = errors


class DigestService:
    """A service for generating "digests" (activity reports)."""

    def __init__(  # pylint:disable=too-many-arguments
        self,
        db,
        h_api,
        mailchimp_service,
        sender,
        email_unsubscribe_service: EmailUnsubscribeService,
    ):
        self._db = db
        self._h_api = h_api
        self._mailchimp_service = mailchimp_service
        self._email_unsubscribe_service = email_unsubscribe_service
        self._sender = sender

    def send_instructor_email_digests(
        self, audience, updated_after, updated_before, override_to_email=None
    ):
        """Send instructor email digests for the given users and timeframe."""
        annotations = self._h_api.get_annotations(
            audience, updated_after, updated_before
        )

        # HAPI.get_annotations() returns an iterable.
        # Turn it into a tuple because we need to iterate over it multiple times.
        annotations = tuple(annotations)

        context = DigestContext(self._db, audience, annotations)

        errors = {}

        for unified_user in context.unified_users:
            digest = context.instructor_digest(unified_user.h_userid)

            if not digest["total_annotations"]:
                # This user has no activity.
                continue

            if override_to_email is None:
                to_email = unified_user.email
            else:
                to_email = override_to_email

            if not to_email:
                # We don't have an email address for this user.
                continue

            try:
                self._mailchimp_service.send_template(
                    "instructor-email-digest",
                    self._sender,
                    recipient=EmailRecipient(to_email, unified_user.display_name),
                    template_vars=digest,
                    unsubscribe_url=self._email_unsubscribe_service.unsubscribe_url(
                        unified_user.h_userid, EmailUnsubscribe.Tag.INSTRUCTOR_DIGEST
                    ),
                )
            except MailchimpError as err:
                errors[unified_user.h_userid] = err
                LOG.exception(err)
                report_exception(err)

        if errors:
            raise SendDigestsError(errors)


@dataclass(frozen=True)
class UnifiedUser:
    """All User's for a given h_userid, unified across all ApplicationInstance's."""

    h_userid: str
    email: Optional[str]
    display_name: Optional[str]


@dataclass(frozen=True)
class UnifiedCourse:
    """All Course's for a given authority_provided_id, unified across all ApplicationInstance's."""

    authority_provided_id: str
    title: Optional[str]
    instructor_h_userids: Tuple[str]
    learner_annotations: Tuple[dict]


class DigestContext:
    """A context/helper object for DigestService."""

    def __init__(self, db, audience, annotations):
        self._db = db
        self.audience = audience
        self.annotations = annotations
        self._unified_users = None
        self._unified_courses = None

    def instructor_digest(self, h_userid):
        """
        Return a digest (dict of template variables) for the given instructor.

        The digest will only include courses in which both:

        1. The user is an instructor
        2. There are annotations by learners
        """
        course_digests = []

        for unified_course in self.unified_courses:
            num_annotations = len(unified_course.learner_annotations)

            if not num_annotations:
                # There was no activity in this course.
                continue

            if h_userid not in unified_course.instructor_h_userids:
                # The user isn't an instructor in this course.
                continue

            course_digests.append(
                {"title": unified_course.title, "num_annotations": num_annotations}
            )

        return {
            "total_annotations": sum(
                course_digest["num_annotations"] for course_digest in course_digests
            ),
            "courses": course_digests,
        }

    @property
    def unified_users(self):
        """Return a list of UnifiedUser's for all the users in self.audience."""
        if self._unified_users is not None:
            return self._unified_users

        query = (
            select(
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
            .where(User.h_userid.in_(self.audience))
            .group_by(User.h_userid)
        )

        self._unified_users = [
            UnifiedUser(row.h_userid, row.email, row.display_name)
            for row in self._db.execute(query)
        ]

        return self._unified_users

    @property
    def unified_courses(self):
        """Return a list of UnifiedCourse's for all the courses in self.annotations."""
        if self._unified_courses is not None:
            return self._unified_courses

        authority_provided_ids = set(
            annotation["group"]["authority_provided_id"]
            for annotation in self.annotations
        )

        # We're going to be joining the grouping table to itself and this requires
        # us to create an alias for one side of the join, see:
        # https://docs.sqlalchemy.org/en/20/orm/self_referential.html#self-referential-query-strategies
        grouping_aliased = aliased(Grouping)

        query = (
            select(
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

        self._unified_courses = []

        for row in self._db.execute(query):
            # SQLAlchemy returns None instead of [].
            authority_provided_ids = row.authority_provided_ids or []
            instructor_h_userids = row.instructor_h_userids or []

            self._unified_courses.append(
                UnifiedCourse(
                    authority_provided_id=row.authority_provided_id,
                    title=row.lms_name,
                    instructor_h_userids=tuple(instructor_h_userids),
                    learner_annotations=tuple(
                        annotation
                        for annotation in self.annotations
                        if annotation["group"]["authority_provided_id"]
                        in authority_provided_ids
                        and annotation["author"]["userid"] not in instructor_h_userids
                    ),
                )
            )

        return self._unified_courses


def service_factory(_context, request):
    return DigestService(
        db=request.db,
        h_api=request.find_service(HAPI),
        mailchimp_service=request.find_service(MailchimpService),
        email_unsubscribe_service=request.find_service(EmailUnsubscribeService),
        sender=EmailSender(
            request.registry.settings.get("mailchimp_digests_subaccount"),
            request.registry.settings.get("mailchimp_digests_email"),
            request.registry.settings.get("mailchimp_digests_name"),
        ),
    )
