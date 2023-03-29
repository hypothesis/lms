from dataclasses import dataclass
from typing import Iterable, Optional, Tuple

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

    def __init__(self, db, h_api, mailchimp_service, sender):
        self._db = db
        self._h_api = h_api
        self._mailchimp_service = mailchimp_service
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

        for h_userid in audience:
            digest = context.instructor_digest(h_userid)

            if not digest["total_annotations"]:
                # This user has no activity.
                continue

            unified_user = context.unified_users[h_userid]

            if override_to_email is None:
                to_email = unified_user.email
            else:
                to_email = override_to_email

            if not to_email:
                # We don't have an email address for this user.
                continue

            self._mailchimp_service.send_template(
                "instructor-email-digest",
                self._sender,
                recipient=EmailRecipient(to_email, unified_user.display_name),
                template_vars=digest,
            )


@dataclass(frozen=True)
class UnifiedUser:
    """All User's for a given h_userid, unified across all ApplicationInstance's."""

    h_userid: str
    user_ids: Tuple[int]
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
        self._audience = audience
        self._annotations = annotations
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

        # Remove duplicates from self.unified_courses.values().
        unified_courses = []
        for unified_course in self.unified_courses.values():
            if unified_course not in unified_courses:
                unified_courses.append(unified_course)

        for unified_course in unified_courses:
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
        """Return a dict mapping h_userid's to UnifiedUser's."""
        if self._unified_users is not None:
            return self._unified_users

        self._unified_users = {}

        h_userids = set(
            self._audience
            + [annotation["author"]["userid"] for annotation in self._annotations]
        )

        for h_userid in h_userids:
            users = self._db.scalars(
                select(User).filter_by(h_userid=h_userid)
                # Order most-recently-updated first so that the code below will
                # use the most recent values for email, display name, etc.
                .order_by(User.updated.desc())
            ).all()

            email = None
            for user in users:
                if user.email:
                    email = user.email
                    break

            display_name = None
            for user in users:
                if user.display_name:
                    display_name = user.display_name
                    break

            self._unified_users[h_userid] = UnifiedUser(
                h_userid=h_userid,
                user_ids=tuple(user.id for user in users),
                email=email,
                display_name=display_name,
            )

        return self._unified_users

    @property
    def unified_courses(self):
        """
        Return a dict mapping authority_provided_id's to UnifiedCourse's.

        Multiple keys in the dict may point to the same UnifiedCourse object,
        meaning that unified_courses.values() may contain duplicates. This
        happens when there are annotations in multiple sub-groupings that
        belong to the same course.
        """
        if self._unified_courses is not None:
            return self._unified_courses

        self._unified_courses = {}

        authority_provided_ids = set(
            annotation["group"]["authority_provided_id"]
            for annotation in self._annotations
        )

        for authority_provided_id in authority_provided_ids:
            if authority_provided_id in self._unified_courses:
                continue

            course_authority_provided_id = self._course_authority_provided_id(
                authority_provided_id
            )

            if not course_authority_provided_id:
                continue

            courses = self._course_groupings(course_authority_provided_id)
            sub_groups = self._sub_groupings(courses)
            instructor_h_userids = self._instructor_h_userids(courses)

            # The authority_provided_ids of all the course groupings and sub-groupings for this course.
            course_authority_provided_ids = set(
                grouping.authority_provided_id for grouping in courses + sub_groups
            )

            # All the learner annotations in this course.
            learner_annotations = [
                annotation
                for annotation in self._annotations
                if annotation["group"]["authority_provided_id"]
                in course_authority_provided_ids
                and annotation["author"]["userid"] not in instructor_h_userids
            ]

            unified_course = UnifiedCourse(
                authority_provided_id=course_authority_provided_id,
                title=courses[0].lms_name,
                instructor_h_userids=instructor_h_userids,
                learner_annotations=tuple(learner_annotations),
            )

            # Map the authority_provided_id's of the course and all its sub-groupings to unified_course.
            for authority_provided_id in course_authority_provided_ids:
                self._unified_courses[authority_provided_id] = unified_course

        return self._unified_courses

    def _course_authority_provided_id(self, authority_provided_id):
        """
        Return the authority_provided_id of the given authority_provided_id's course.

        In the case of a course group this will return the given
        authority_provided_id itself.

        In the case of a sub-group this will return the authority_provided_id
        of the course group that the sub-group belongs to.
        """
        first_grouping = self._db.scalars(
            select(Grouping).filter_by(authority_provided_id=authority_provided_id)
        ).first()

        if not first_grouping:
            return None

        if first_grouping.type == Grouping.Type.COURSE:
            return first_grouping.authority_provided_id

        assert first_grouping.parent.type == Grouping.Type.COURSE
        return first_grouping.parent.authority_provided_id

    def _course_groupings(self, authority_provided_id):
        """
        Return all course groupings with the given authority_provided_id.

        When an LMS has multiple application instances this may return multiple
        course groupings with the same authority_provided_id but different
        application instances.
        """
        return self._db.scalars(
            select(Course).filter_by(authority_provided_id=authority_provided_id)
            # Sort by updated so that we use the most recently updated courses
            # first when picking a course title etc.
            .order_by(Course.updated.desc())
        ).all()

    def _sub_groupings(self, course_groupings):
        """Return all sub-groupings of the given course groupings."""
        return self._db.scalars(
            select(Grouping).filter(
                Grouping.parent_id.in_([course.id for course in course_groupings])
            )
        ).all()

    def _instructor_h_userids(self, courses):
        """Return the h_userids of all instructors in the given courses."""
        return tuple(
            unified_user.h_userid
            for unified_user in self.unified_users.values()
            if self._is_instructor(unified_user, courses)
        )

    def _is_instructor(
        self, unified_user: UnifiedUser, courses: Iterable[Course]
    ) -> bool:
        """Return True if `user` is an instructor in any of `courses`."""
        return bool(
            self._db.scalar(
                select(func.count())
                .select_from(AssignmentMembership)
                .join(Assignment)
                .join(AssignmentGrouping)
                .join(LTIRole)
                .filter(
                    AssignmentGrouping.grouping_id.in_(
                        (course.id for course in courses)
                    )
                )
                .filter(AssignmentMembership.user_id.in_(unified_user.user_ids))
                .filter(LTIRole.type == "instructor", LTIRole.scope == "course")
            )
        )


def service_factory(_context, request):
    return DigestService(
        db=request.db,
        h_api=request.find_service(HAPI),
        mailchimp_service=request.find_service(MailchimpService),
        sender=EmailSender(
            request.registry.settings.get("mailchimp_digests_subaccount"),
            request.registry.settings.get("mailchimp_digests_email"),
            request.registry.settings.get("mailchimp_digests_name"),
        ),
    )
