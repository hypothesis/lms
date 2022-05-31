"""A service for managing `GroupInfo` records."""

from lms.models import ApplicationInstance, GroupInfo, Grouping

__all__ = ["GroupInfoService"]


class GroupInfoService:
    """A service for managing `GroupInfo` records."""

    def __init__(self, _context, request):
        self._db = request.db
        self._lti_user = request.lti_user

    _GROUPING_TYPES = {
        "course": "course_group",
        "canvas_section": "section_group",
        "canvas_group": "canvas_group_group",
        "blackboard_group": "blackboard_group_group",
    }

    def upsert_group_info(
        self,
        grouping: Grouping,
        application_instance: ApplicationInstance,
        params: dict,
    ):
        """
        Upsert a row into the `group_info` DB table.

        :param grouping: grouping to upsert based on
        :param application_instance: ApplicationInstance this group belongs to
        :param params: columns to set on the row ("authority_provided_id",
            "id", "info" and any non-matching items will be ignored)
        """
        group_info = (
            self._db.query(GroupInfo)
            .filter_by(authority_provided_id=grouping.authority_provided_id)
            .one_or_none()
        )

        if not group_info:
            group_info = GroupInfo(
                authority_provided_id=grouping.authority_provided_id,
                application_instance=application_instance,
            )
            self._db.add(group_info)

        group_info.type = self._GROUPING_TYPES[grouping.type]
        group_info.application_instance_id = application_instance.id
        group_info.update_from_dict(
            params, skip_keys={"authority_provided_id", "id", "info"}
        )

        if self._lti_user.is_instructor:
            group_info.upsert_instructor(
                dict(email=self._lti_user.email, **self._lti_user.h_user._asdict())
            )
