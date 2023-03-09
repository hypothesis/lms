from dataclasses import dataclass, field
from typing import List, Optional

from sqlalchemy import func, select

from lms.models import (
    Assignment,
    AssignmentGrouping,
    AssignmentMembership,
    Course,
    Grouping,
    LTIRole,
    User,
)
from lms.services.h_api import HAPI
from lms.services.mailchimp import EmailRecipient, EmailSender, MailchimpService


class DigestService:
    """A service for generating "digests" (activity reports)."""

    def __init__(
        self, db, helper, h_api, mailchimp_service, sender
    ):  # pylint:disable=too-many-arguments
        self.db = db
        self.helper = helper
        self.h_api = h_api
        self.mailchimp_service = mailchimp_service
        self.sender = sender

    def send_instructor_email_digests(
        self, h_userids, updated_after, updated_before, override_to_email=None
    ):
        """Send instructor email digests for the given users and timeframe."""
        annotations = self.h_api.get_annotations(
            h_userids, updated_after, updated_before
        )
        unified_courses = self.helper.unified_courses(annotations)

        for h_userid in h_userids:
            unified_user = UnifiedUser.make(self.db, h_userid)
            digest = self.helper.instructor_digest(unified_user, unified_courses)

            if not digest["total_annotations"]:
                continue

            if override_to_email is None:
                to_email = unified_user.email
            else:
                to_email = override_to_email

            self.mailchimp_service.send_template(
                "instructor-email-digest",
                self.sender,
                recipient=EmailRecipient(to_email, unified_user.display_name),
                template_vars=digest,
            )


@dataclass
class UnifiedUser:
    """All User's for a given h_userid, unified across all ApplicationInstance's."""

    users: List[User]

    @property
    def h_userid(self) -> str:
        """Return this user's h_userid."""
        return self.users[0].h_userid

    @property
    def user_ids(self) -> List[int]:
        """Return the User.id's of all the users with self.h_userid."""
        return [user.id for user in self.users]

    @property
    def email(self) -> Optional[str]:
        """Return an email address for this user."""
        for user in self.users:
            if user.email:
                return user.email

        return None

    @property
    def display_name(self) -> Optional[str]:
        """Return a display name for this user."""
        for user in self.users:
            if user.display_name:
                return user.display_name

        return None

    @classmethod
    def make(cls, db, h_userid):
        """Return a UnifiedUser for the given h_userid."""
        return cls(
            db.scalars(
                select(User).filter_by(h_userid=h_userid)
                # Order most-recently-updated first so that the methods above
                # will use the most recent values for email, display name, etc.
                .order_by(User.updated.desc())
            ).all()
        )


@dataclass
class UnifiedCourse:
    """All Course's for a given authority_provided_id, unified across all ApplicationInstance's."""

    courses: List[Course]
    annotations: List[dict] = field(default_factory=list)

    @property
    def authority_provided_id(self) -> str:
        """Return this course's authority_provided_id."""
        return self.courses[0].authority_provided_id

    @property
    def title(self) -> str:
        """Return a title for this course."""
        return self.courses[0].lms_name

    def learner_annotations(self, db) -> List[dict]:
        """Return a list of all learner annotations in this course."""
        return [
            annotation
            for annotation in self.annotations
            if not self.is_instructor(
                db, UnifiedUser.make(db, annotation["author"]["userid"])
            )
        ]

    def is_instructor(self, db, user: UnifiedUser) -> bool:
        """Return True if `user` is an instructor in this course."""
        course_ids = [course.id for course in self.courses]

        return bool(
            db.scalar(
                select(func.count())
                .select_from(AssignmentMembership)
                .join(Assignment)
                .join(AssignmentGrouping)
                .join(LTIRole)
                .filter(AssignmentGrouping.grouping_id.in_(course_ids))
                .filter(AssignmentMembership.user_id.in_(user.user_ids))
                .filter(LTIRole.type == "instructor", LTIRole.scope == "course")
            )
        )

    @staticmethod
    def get_courses(db, authority_provided_id):
        """Return a list of all Course's with the given authority_provided_id."""
        return db.scalars(
            select(Course)
            .filter_by(authority_provided_id=authority_provided_id)
            .order_by(Course.updated.desc())
        ).all()

    @classmethod
    def make(cls, db, authority_provided_id):
        """Return a UnifiedCourse for the given authority_provided_id."""
        # There may be multiple groupings with the same authority_provided_id
        # but different application instances.
        #
        # When that happens their parent course groupings might have different
        # authority_provided_id's and maybe we should collect together all the
        # course groupings with any of those parent authority_provided_id's.
        #
        # But this is probably a rare or non-existent edge case and it's not
        # clear that it's actually valid to collect together course groupings
        # with different authority_provided_id's into a single UnifiedCourse.
        #
        # So keep it simple by only considering the most recently updated
        # grouping.
        first_grouping = db.scalars(
            select(Grouping)
            .filter_by(authority_provided_id=authority_provided_id)
            .order_by(Grouping.updated.desc())
        ).first()

        if not first_grouping:
            raise UnknownAuthorityProvidedID()

        if first_grouping.type == Grouping.Type.COURSE:
            course_authority_provided_id = first_grouping.authority_provided_id
        else:
            assert first_grouping.parent.type == Grouping.Type.COURSE
            course_authority_provided_id = first_grouping.parent.authority_provided_id

        return cls(cls.get_courses(db, course_authority_provided_id))


class DigestHelper:
    """Helper methods for DigestService."""

    def __init__(self, db):
        self.db = db

    def unified_courses(self, annotations) -> List[UnifiedCourse]:
        """
        Return the given list of annotation dicts organized by course.

        >>> helper.annotations_by_course([{annotation}, ...])
        [
            UnifiedCourse(authority_provided_id="id1", annotations=[{annotation}, ...]),
            UnifiedCourse(authority_provided_id="id2", annotations=[{annotation}, ...]),
            ...
        }
        """
        unified_courses = {}

        for annotation in annotations:
            authority_provided_id = annotation["group"]["authority_provided_id"]

            try:
                unified_course = UnifiedCourse.make(self.db, authority_provided_id)
            except UnknownAuthorityProvidedID:
                continue

            unified_course = unified_courses.setdefault(
                unified_course.authority_provided_id, unified_course
            )
            unified_course.annotations.append(annotation)

        return list(unified_courses.values())

    def instructor_digest(
        self, instructor: UnifiedUser, unified_courses: List[UnifiedCourse]
    ):
        """
        Return a dict of digest variables for the given instructor and unified_courses.

        The digest will only include courses in which both:

        1. The user is an instructor
        2. There are annotations by learners
        """
        course_digests = []

        for unified_course in unified_courses:
            num_annotations = len(unified_course.learner_annotations(self.db))

            if not num_annotations:
                continue

            if not unified_course.is_instructor(self.db, instructor):
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


class UnknownAuthorityProvidedID(Exception):
    """A given authority_provided_id couldn't be found in the DB."""


def service_factory(_context, request):
    return DigestService(
        db=request.db,
        helper=DigestHelper(request.db),
        h_api=request.find_service(HAPI),
        mailchimp_service=request.find_service(MailchimpService),
        sender=EmailSender(
            request.registry.settings.get("mailchimp_digests_subaccount"),
            request.registry.settings.get("mailchimp_digests_email"),
            request.registry.settings.get("mailchimp_digests_name"),
        ),
    )
