from sqlalchemy import func

from lms.models import (
    Grouping,
    LMSCourse,
    LMSSegment,
    LMSSegmentMembership,
    LMSUser,
    LTIRole,
)
from lms.services.group_set import GroupSetService
from lms.services.upsert import bulk_upsert


class SegmentService:
    def __init__(self, db, group_set_service: GroupSetService):
        self._db = db
        self._group_set_service = group_set_service

    def upsert_segments(
        self,
        course: LMSCourse,
        type_: Grouping.Type,
        groupings: list[Grouping],
        lms_group_set_id: str | None = None,
    ) -> list[LMSSegment]:
        group_set = None
        if lms_group_set_id:
            group_set = self._group_set_service.find_group_set(
                course.course.application_instance,
                lms_id=lms_group_set_id,
                context_id=course.lti_context_id,
            )

        return bulk_upsert(
            self._db,
            LMSSegment,
            [
                {
                    "type": type_,
                    "lms_id": segment.lms_id,
                    "name": segment.lms_name,
                    "h_authority_provided_id": segment.authority_provided_id,
                    "lms_course_id": course.id,
                    "lms_group_set_id": group_set.id if group_set else None,
                }
                for segment in groupings
            ],
            index_elements=["h_authority_provided_id"],
            update_columns=["name", "updated"],
        ).all()

    def upsert_segment_memberships(
        self,
        lms_user: LMSUser,
        lti_roles: list[LTIRole],
        segments: list[LMSSegment],
    ) -> list[LMSSegmentMembership]:
        if not lms_user.id or any(s.id is None for s in segments):
            # Ensure all ORM objects have their PK populated
            self._db.flush()

        return bulk_upsert(
            self._db,
            LMSSegmentMembership,
            [
                {
                    "lms_segment_id": s.id,
                    "lms_user_id": lms_user.id,
                    "lti_role_id": lti_role.id,
                    "updated": func.now(),
                }
                for s in segments
                for lti_role in lti_roles
            ],
            index_elements=["lms_segment_id", "lms_user_id", "lti_role_id"],
            update_columns=["updated"],
        )


def factory(_context, request):
    return SegmentService(
        db=request.db, group_set_service=request.find_service(GroupSetService)
    )
