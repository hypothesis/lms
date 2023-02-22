from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from typing import Dict, List, NewType, Optional

from lms.models import (
    Assignment,
    AssignmentGrouping,
    AssignmentMembership,
    Course,
    Grouping,
    LTIRole,
    User,
)
from lms.services import h_api


@dataclass
class UserRecords:
    """All models.User rows for a given h_userid."""

    h_userid: str
    user_records: List[User] = field(default_factory=list)

    def __post_init__(self):
        for user_record in self.user_records:
            assert user_record.h_userid == self.h_userid

    @property
    def email(self) -> Optional[str]:
        for user_record in self.user_records:
            if user_record.email:
                return user_record.email

        return None

    @property
    def name(self) -> Optional[str]:
        for user_record in self.user_records:
            if user_record.display_name:
                return user_record.display_name

        return None

    @classmethod
    def make(cls, db, h_userid):
        return cls(
            h_userid,
            db.query(User)
            .filter_by(h_userid=h_userid)
            .order_by(User.updated.desc())
            .all(),
        )


@dataclass
class CourseGroupings:
    """A course including all its groupings (across all application instances)."""

    course_groupings: List[Course] = field(default_factory=list)

    def __post_init__(self):
        for grouping in self.course_groupings:
            assert grouping.authority_provided_id == self.authority_provided_id

    @property
    def authority_provided_id(self) -> str:
        return self.course_groupings[0].authority_provided_id

    @property
    def title(self) -> str:
        return self.course_groupings[0].lms_name

    @property
    def grouping_ids(self) -> List[int]:
        return [grouping.id for grouping in self.course_groupings]

    def is_instructor(self, db, user: h_api.User) -> bool:
        user_ids = [
            user.id for user in db.query(User).filter_by(h_userid=user.username)
        ]

        return bool(
            db.query(AssignmentMembership)
            .join(Assignment)
            .join(AssignmentGrouping)
            .join(LTIRole)
            .filter(AssignmentGrouping.grouping_id.in_(self.grouping_ids))
            .filter(AssignmentMembership.user_id.in_(user_ids))
            .filter(LTIRole.type == "instructor", LTIRole.scope == "course")
            .count()
        )

    @classmethod
    @lru_cache
    def make(cls, db, authority_provided_id):
        groupings = (
            db.query(Grouping)
            .filter_by(authority_provided_id=authority_provided_id)
            .all()
        )

        if not groupings:
            raise _UnknownAuthorityProvidedID()

        course_groupings = []
        for grouping in groupings:
            if grouping.type == Grouping.Type.COURSE:
                course_grouping = grouping
            else:
                assert grouping.parent.type == Grouping.Type.COURSE
                course_grouping = grouping.parent

            course_groupings.append(course_grouping)

        return cls(course_groupings)


@dataclass
class CourseDigest:
    course: CourseGroupings
    users: Dict[h_api.User, List[h_api.Annotation]] = field(default_factory=dict)


AuthorityProvidedID = NewType("AuthorityProvidedID", str)


@dataclass
class InstructorDigest:
    user: UserRecords
    courses: Dict[AuthorityProvidedID, CourseDigest]


HUserID = NewType("HUserID", str)
InstructorDigests = Dict[HUserID, InstructorDigest]


class DigestService:
    def __init__(self, db, h_api_svc):
        self.db = db
        self.h_api = h_api_svc

    def get_instructor_digest(
        self, audience: List[str], since: datetime, until: datetime
    ) -> InstructorDigests:
        """Return instructor digest data for the given audience and time range."""
        annotations = self.h_api.get_annotations(audience, since, until)
        course_digests = {}

        for annotation in annotations:
            try:
                course = CourseGroupings.make(
                    self.db, annotation.group.authority_provided_id
                )
            except _UnknownAuthorityProvidedID:
                continue

            if course.is_instructor(self.db, annotation.user):
                continue

            course_digest = course_digests.setdefault(
                course.authority_provided_id, CourseDigest(course=course)
            )

            user_annotations = course_digest.users.setdefault(annotation.user, [])
            user_annotations.append(annotation)

        user_digests = {}
        for h_userid in audience:
            user_course_digests = {}
            for authority_provided_id, course_digest in course_digests.items():
                if course_digest.course.is_instructor(
                    self.db, h_api.User(username=h_userid)
                ):
                    user_course_digests[authority_provided_id] = course_digest

            user_digests[h_userid] = InstructorDigest(
                UserRecords.make(self.db, h_userid), user_course_digests
            )

        return user_digests


class _UnknownAuthorityProvidedID(Exception):
    """A given authority_provided_id couldn't be found in the DB."""


def factory(_context, request):
    return DigestService(request.db, request.find_service(name="h_api"))
