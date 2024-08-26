from logging import getLogger

from sqlalchemy import select

from lms.models import (
    ApplicationInstance,
    LMSCourse,
    LMSCourseApplicationInstance,
    LTIRegistration,
)
from lms.services.lti_names_roles import LTINamesRolesService

LOG = getLogger(__name__)


class CourseRosterService:
    def __init__(self, db, lti_names_roles_service: LTINamesRolesService):
        self._db = db
        self._lti_names_roles_service = lti_names_roles_service

    def fetch_roster(self, lms_course: LMSCourse) -> None:
        lti_registration = self._db.scalars(
            select(LTIRegistration)
            .join(ApplicationInstance)
            .join(LMSCourseApplicationInstance)
            .where(LMSCourseApplicationInstance.lms_course_id == lms_course.id)
            .order_by(LTIRegistration.updated.desc())
        ).first()

        assert lti_registration, "No LTI registration found for LMSCourse."
        assert (
            lms_course.lti_context_memberships_url
        ), "Trying fetch roster for course without service URL."

        roster = self._lti_names_roles_service.get_context_memberships(
            lti_registration, lms_course.lti_context_memberships_url
        )
        LOG.info(
            "Roster for %s. Users returned %s",
            lms_course.h_authority_provided_id,
            len(roster),
        )


def factory(_context, request):
    return CourseRosterService(
        db=request.db,
        lti_names_roles_service=request.find_service(LTINamesRolesService),
    )
